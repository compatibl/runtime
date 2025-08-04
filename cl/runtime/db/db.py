# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from abc import ABC
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence
from more_itertools import consume
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.db_key import DbKey
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.key_util import KeyUtil
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.table_binding_key_query_by_record_type import TableBindingKeyQueryByRecordType
from cl.runtime.records.table_binding_key_query_by_table import TableBindingKeyQueryByTable
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.db_settings import DbSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin, ABC):
    """Polymorphic data storage with dataset isolation."""

    _table_binding_cache: dict[tuple[str, str], TableBinding] | None = None
    """Cache of table to record type bindings for records stored in this DB."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    def get_bindings(self) -> tuple[TableBinding, ...]:
        """
        Return table to record type bindings in alphabetical order of table name followed by record type name.

        Notes:
            More than one table can exist for the same record type and vice versa.
        """
        # Load from DB as cache may be out of date
        bindings = self.load_type(TableBinding, cast_to=TableBinding)

        # Sort bindings by table name and then by key type
        return tuple(sorted(bindings, key=lambda x: (x.table, x.record_type)))

    def get_tables(self) -> tuple[str, ...]:
        """Return DB table names in alphabetical order of non-delimited PascalCase format."""

        # Bindings may include multiple entries with the same table name
        bindings = self.get_bindings()

        # Convert to set to remove duplicates, sort in alphabetical order, convert back to tuple
        return tuple(sorted(set(binding.table for binding in bindings)))

    def get_record_type_names(self) -> tuple[str, ...]:
        """
        Return non-delimited PascalCase record type names in alphabetical order for records stored in this DB.

        Notes:
            More than one table can exist for the same record type.
        """
        # Bindings may include multiple entries with the same record type
        bindings = self.get_bindings()

        # Convert to set to remove duplicates and then back to tuple with sorting in alphabetical order
        return tuple(sorted(set(binding.record_type for binding in bindings)))

    def get_bound_tables(self, *, record_type: type[RecordProtocol] | str) -> tuple[str, ...]:
        """
        Return tables for the specified record type or name in alphabetical order.

        Returns:
            Table names in non-delimited PascalCase format.

        Args:
            record_type: Record type or name for which the tables are returned.
        """
        # Query by record type, each parent type has its own binding record
        record_type = TypeUtil.name(record_type) if isinstance(record_type, type) else record_type
        query = TableBindingKeyQueryByRecordType(record_type=record_type).build()
        bindings = self.load_where(query, cast_to=TableBinding)

        # Convert to set to remove duplicates, sort in alphabetical order, convert back to tuple
        return tuple(sorted(set(binding.table for binding in bindings)))

    def get_bound_key_type(self, *, table: str) -> type:
        """
        Key type for the specified table, table must exist.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        # Query by record type, each parent type has its own binding record
        query = TableBindingKeyQueryByTable(table=table).build()
        bindings = self.load_where(query, cast_to=TableBinding)
        if not bindings:
            raise RuntimeError(f"Table {table} is not found.")

        # Convert to set to remove duplicates
        key_type_names = tuple(set(binding.key_type for binding in bindings))

        # Error if more than one key type is found
        if len(key_type_names) > 1:
            key_type_names_str = "\n".join(sorted(key_type_names))
            raise RuntimeError(f"Multiple key types found in table {table}:\n{key_type_names_str}")

        key_type = TypeCache.get_class_from_type_name(key_type_names[0])
        return key_type

    def get_bound_record_type_names(self, *, table: str) -> tuple[str, ...]:
        """
        Record type names actually stored in the specified table, table must exist.

        Returns:
            Tuple of non-delimited PascalCase record type names in alphabetical order or an empty tuple.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        # Query by record type, each parent type has its own binding record
        query = TableBindingKeyQueryByTable(table=table).build()
        bindings = self.load_where(query, cast_to=TableBinding)
        if not bindings:
            raise RuntimeError(f"Table {table} is not found.")

        # Convert to set to remove duplicates, sort in alphabetical order, convert back to tuple
        return tuple(sorted(set(binding.record_type for binding in bindings)))

    def get_allowed_record_type_names(self, *, table: str) -> tuple[str, ...]:
        """
        Record type names that may be stored in the specified table, table must exist.

        Returns:
            Tuple of non-delimited PascalCase record type names in alphabetical order.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        # Bound key type exists if the table exists
        key_type = self.get_bound_key_type(table=table)

        # Return child names of the bound key type
        result = TypeCache.get_child_names(key_type)
        return result

    def get_lowest_bound_record_type_name(self, *, table: str) -> str:
        """
        Return the name of the lowest common type for the record types bound to the table, error if the table is empty.

        Returns:
            Non-delimited PascalCase record type name.

        Args:
            table: Table name in non-delimited PascalCase format.
        """

        # The result may be empty if the table is empty
        bound_type_names = self.get_bound_record_type_names(table=table)

        # The case of empty bound_type_names can only occur if table name is stale because bindings
        # will include at least one record type when data is added, raise an error
        if not bound_type_names:
            raise RuntimeError(f"Table {table} is not found.")
        result = TypeCache.get_common_base_name(record_types=bound_type_names) if bound_type_names else None
        return result

    def load_one(
        self,
        record_or_key: TKey,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """

        # TODO: This is a temporary safeguard, remove after verification
        if isinstance(record_or_key, type):
            raise RuntimeError("Code update error for load_one signature.")

        if record_or_key is not None:
            result = self.load_one_or_none(record_or_key, dataset=dataset, cast_to=cast_to)
            if result is None:
                cast_to_str = f"\nwhen loading type {TypeUtil.name(cast_to)}" if cast_to else ""
                raise RuntimeError(
                    f"Record not found for key {KeyUtil.format(record_or_key)}{cast_to_str}.\n"
                    f"Use 'load_one_or_none' method to return None instead of raising an error."
                )
            return result
        else:
            cast_to_str = f"\nwhen loading type {TypeUtil.name(cast_to)}" if cast_to else ""
            raise RuntimeError(
                f"Parameter 'record_or_key' is None for load_one method{cast_to_str}.\n"
                f"Use 'load_one_or_none' method to return None instead of raising an error."
            )

    def load_one_or_none(
        self,
        record_or_key: TKey | None,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """

        # TODO: This is a temporary safeguard, remove after verification
        if isinstance(record_or_key, type):
            raise RuntimeError("Code update error for load_one_or_none signature.")

        result = self.load_many([record_or_key], dataset=dataset, cast_to=cast_to)
        if len(result) == 1:
            return result[0]
        else:
            raise RuntimeError("DataContext.load_many returned more records than requested.")

    def load_many(
        self,
        records_or_keys: Sequence[TRecord | TKey | None] | None,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """

        # Pass through None or an empty sequence
        if not records_or_keys:
            return records_or_keys

        # Check that the input list consists of only None, records, or keys
        self._check_invalid_inputs(records_or_keys)

        # Perform these checks if cast_to is specified
        if cast_to is not None:
            # Check that the keys in the input list have the same type as cast_to.get_key_type()
            key_type = cast_to.get_key_type()
            invalid_keys = [x for x in records_or_keys if is_key(x) and not isinstance(x, key_type)]
            if len(invalid_keys) > 0:
                invalid_keys_str = "\n".join(str(x) for x in invalid_keys)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataContext includes the following keys\n"
                    f"whose type is not the same as the key type {TypeUtil.name(key_type)}\n"
                    f"of the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_keys_str}"
                )
            # Check that the records in the input list are derived from cast_to
            invalid_records = [x for x in records_or_keys if is_record(x) and not isinstance(x, cast_to)]
            if len(invalid_records) > 0:
                invalid_records_str = "\n".join(str(x) for x in invalid_records)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataContext includes the following records\n"
                    f"that are not derived from the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_records_str}"
                )

        # Check that all records or keys in object format are frozen
        self._check_frozen_inputs(records_or_keys)

        # The list of keys to load, skip None and records
        keys_to_load = [x for x in records_or_keys if is_key(x)]

        # Group keys by table
        keys_to_load_grouped_by_table = self._group_inputs_by_table(keys_to_load)

        # Get records from DB, the result is unsorted and grouped by table
        loaded_records_grouped_by_table = [
            self.load_many_unsorted(table, table_keys, dataset=dataset)
            for table, table_keys in keys_to_load_grouped_by_table.items()
        ]

        # Concatenated list
        loaded_records = [item for sublist in loaded_records_grouped_by_table for item in sublist]
        serialized_loaded_keys = [KeySerializers.TUPLE.serialize(x.get_key()) for x in loaded_records]

        # Create a dictionary with pairs consisting of serialized key (after normalization) and the record for this key
        loaded_records_dict = {k: v for k, v in zip(serialized_loaded_keys, loaded_records)}

        # Populate the result with records loaded using input keys, pass through None and input records
        result = tuple(
            loaded_records_dict.get(KeySerializers.TUPLE.serialize(x), None) if is_key(x) else x
            for x in records_or_keys
        )

        # Cast to cast_to if specified
        if cast_to is not None:
            result = tuple(CastUtil.cast(cast_to, x) for x in result)
        return result

    def load_type(
        self,
        filter_to: type[TRecord],
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records of 'filter_to' type and its subtypes from all tables where they are stored.

        Args:
            filter_to: The query will return only this type and its subtypes
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

        # Get the list of tables where this type is stored
        tables = self.get_bound_tables(record_type=filter_to)

        tables_len = len(tables)
        if tables_len == 0:

            # There are no tables where this type is stored, return an empty tuple
            return tuple()
        elif tables_len == 1:

            # Handle static tables (one table per type) separately by delegating to load_table
            return self.load_table(
                tables[0],
                dataset=dataset,
                cast_to=cast_to,
                filter_to=filter_to,
                project_to=project_to,
                limit=limit,
                skip=skip,
            )
        else:
            # Handle the case of multiple tables

            # Validate limit and handle the limit=0 case separately
            if limit is not None:
                if limit > 0:
                    # Limit is set
                    remaining_limit = limit
                elif limit == 0:
                    # Handle limit=0 separately because pymongo interprets limit=0 as no limit,
                    # while we return an empty tuple
                    return tuple()
                else:
                    raise RuntimeError(f"Parameter limit={limit} is negative.")
            else:
                # No limit
                remaining_limit = None

            # Validate skip and replace None by 0 (both mean do not skip)
            if skip is not None:
                if skip >= 0:
                    # Positive or zero values are both valid
                    remaining_skip = skip
                else:
                    raise RuntimeError(f"Parameter skip={skip} is negative.")
            else:
                # Normalize to 0 for do not skip
                remaining_skip = 0

            result = []
            for table in tables:

                if remaining_limit is not None:
                    # Handle the case with limit
                    if remaining_limit > 0:
                        # Pull enough rows from this table to satisfy remaining skip + limit
                        table_limit = remaining_skip + remaining_limit
                    elif remaining_limit == 0:
                        # Limit reached, break the loop over tables
                        break
                    else:
                        # The update logic should guarantee non-negative value, handle a possible error
                        raise RuntimeError(f"Parameter remaining_limit={remaining_limit} must be positive.")
                else:
                    # Otherwise pull from this table with no limit
                    table_limit = None

                table_result = self.load_table(
                    table,
                    dataset=dataset,
                    cast_to=cast_to,
                    filter_to=filter_to,
                    project_to=project_to,
                    limit=table_limit,
                    skip=None,  # Global skip is handled below
                )

                # Apply global skip
                if remaining_skip:
                    if remaining_skip >= len(table_result):
                        remaining_skip -= len(table_result)
                        continue
                    table_result = table_result[remaining_skip:]
                    remaining_skip = 0

                # Apply global limit
                if remaining_limit is not None:
                    if remaining_limit >= len(table_result):
                        result.extend(table_result)
                        remaining_limit -= len(table_result)
                    else:
                        result.extend(table_result[:remaining_limit])
                        break
                else:
                    # No limit is set
                    result.extend(table_result)

            return tuple(result)

    @abstractmethod
    def load_table(
        self,
        table: str,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records from the specified table.

        Args:
            table: The table from which the records are loaded
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

    @abstractmethod
    def load_many_unsorted(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> Sequence[RecordMixin]:
        """
        Load records from the specified table for a sequence of primary key tuples.
        The result is unsorted and skips the records that are not found.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            keys: A sequence of keys in (key_type_or_type_name, *primary_keys) format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

    @abstractmethod
    def load_where(
        self,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

    def save_many(
        self,
        records: Sequence[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            records: Iterable of records.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        if not records:
            return

        # Validate inputs. Allowed values are records and None.
        self._check_invalid_inputs(records, key_allowed=False)
        self._check_frozen_inputs(records)

        # Group records by table
        records_grouped_by_table = self._group_inputs_by_table(records)

        # Save records for each table
        [
            self.save_many_grouped(table, table_records, dataset=dataset)
            for table, table_records in records_grouped_by_table.items()
        ]

    @abstractmethod
    def save_many_grouped(
        self,
        table: str,
        records: Sequence[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records grouped by table to the specified table in storage.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            records: Iterable of records.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

    def delete_many(
        self,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

        Args:
            keys: Iterable of keys.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        if not keys:
            return

        # Validate inputs. Allowed values are keys and None.
        self._check_invalid_inputs(keys, record_allowed=False)
        self._check_frozen_inputs(keys)

        keys_grouped_by_table = self._group_inputs_by_table(keys)

        [
            self.delete_many_grouped(table, table_records, dataset=dataset)
            for table, table_records in keys_grouped_by_table.items()
        ]

    @abstractmethod
    def delete_many_grouped(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys grouped by table.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            keys: Iterable of keys.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

    @abstractmethod
    def count_where(
        self,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        filter_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            filter_to: Count only the subtypes of this type (defaults to the query target type)
        """

    @abstractmethod
    def drop_test_db(self) -> None:
        """
        Drop a database as part of a unit test.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - The method is invoked from a unit test based on ProcessContext.is_testing()
        - db_id starts with db_test_prefix specified in settings.yaml (the default prefix is 'test_')
        """

    @abstractmethod
    def drop_temp_db(self, *, user_approval: bool) -> None:
        """
        Drop a temporary database with explicit user approval.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - user_approval is true
        - db_id starts with db_temp_prefix specified in settings.yaml (the default prefix is 'temp_')
        """

    @abstractmethod
    def close_connection(self) -> None:
        """Close database connection to releasing resource locks."""

    @classmethod
    def _get_test_db_name(cls) -> str:  # TODO: Use fixture instead
        """Get SQLite database with name based on test namespace."""
        if ProcessContext.is_testing():
            result = f"temp;{QaUtil.get_test_name().replace('.', ';')}"
            return result
        else:
            raise RuntimeError("Attempting to get test DB name outside a test.")

    @classmethod
    def create(cls, *, db_type: type | None = None, db_id: str | None = None):
        """Create DB of the specified type, or use DB type from context settings if not specified."""

        # Get DB settings instance for the lookup of defaults
        db_settings = DbSettings.instance()

        # Get DB type from context settings if not specified
        if db_type is None:
            db_type = TypeCache.get_class_from_type_name(db_settings.db_type)

        # Get DB identifier if not specified
        if db_id is None:
            if not ProcessContext.is_testing():
                db_id = db_settings.db_id
            else:
                raise RuntimeError("Use pytest fixtures to create temporary DBs inside tests.")

        # Create and return a new DB instance
        result = db_type(db_id=db_id)
        return result

    def _add_binding(self, *, table: str, record_type: type[RecordProtocol]) -> None:
        """
        Record the table to record type binding in the DB if not found in cache, update cache.

        Args:
            table: Table name in non-delimited PascalCase format
            record_type: Record type bound to the table
        """

        # Initialize the table binding cache from the DB table if not yet initialized
        if not self._table_binding_cache:
            query = TableBindingKeyQueryByTable().build()
            bindings = self.load_where(query, cast_to=TableBinding)
            self._table_binding_cache = {(binding.table, binding.record_type): binding for binding in bindings}

        record_type_name = TypeUtil.name(record_type)
        cache_key = (table, record_type_name)
        if cache_key not in self._table_binding_cache:

            # If the binding is not yet in cache, write bindings for this and all parent record types
            # to DB as it is faster to overwrite than to check for each parent

            # Create binding for each parent and self
            parent_type_names = TypeCache.get_parent_names(record_type)
            key_type_name = TypeUtil.name(record_type.get_key_type())
            bindings = tuple(
                TableBinding(
                    table=table,
                    record_type=parent_type_name,
                    key_type=key_type_name,
                ).build()
                for parent_type_name in parent_type_names
            )

            # Add to cache
            consume(
                self._table_binding_cache.setdefault((binding.table, binding.record_type), binding)
                for binding in bindings
            )

            # Save to DB
            self.save_many(bindings)

    def check_drop_test_db_preconditions(self) -> None:
        """Error if db_id does not start from db_test_prefix specified in settings.yaml (defaults to 'test_')."""
        if not ProcessContext.is_testing():
            raise RuntimeError(f"Cannot drop a unit test DB when not invoked from a running unit test.")

        db_settings = DbSettings.instance()
        if not self.db_id.startswith(db_settings.db_test_prefix):
            raise RuntimeError(
                f"Cannot drop a unit test DB from code because its db_id={self.db_id}\n"
                f"does not start from unit test DB prefix '{db_settings.db_test_prefix}'."
            )

    def check_drop_temp_db_preconditions(self, *, user_approval: bool) -> None:
        """
        Check user approval and raise an error if db_id does not start from db_temp_prefix
        specified in settings.yaml (defaults to 'temp_').
        """
        if not user_approval:
            raise RuntimeError(f"Cannot drop a temporary DB from code without explicit user approval.")

        db_settings = DbSettings.instance()
        if not self.db_id.startswith(db_settings.db_temp_prefix):
            raise RuntimeError(
                f"Cannot drop a DB from code even with user approval because its db_id={self.db_id}\n"
                f"does not start from temporary DB prefix '{db_settings.db_temp_prefix}'."
            )

    @classmethod
    def _check_frozen_inputs(cls, inputs: Sequence[TRecord | TKey | None]) -> None:
        """Check that all records or keys in object format are frozen."""

        unfrozen_inputs = [x for x in inputs if x is not None and not x.is_frozen()]
        if len(unfrozen_inputs) > 0:
            caller_name = sys._getframe(1).f_code.co_name
            unfrozen_inputs_str = "\n".join(str(x) for x in unfrozen_inputs)
            raise RuntimeError(
                f"Inputs of {caller_name} method includes\n"
                f"the following items that are not frozen:\n{unfrozen_inputs_str}"
            )

    @classmethod
    def _check_invalid_inputs(
        cls,
        inputs: Sequence[TRecord | TKey | None],
        *,
        key_allowed: bool = True,
        record_allowed: bool = True,
        none_allowed: bool = True,
    ) -> None:
        """
        Check that the input list consists of only None, records, or keys.
        Use flags 'key_allowed', 'record_allowed', and 'none_allowed' to control the list of valid values.
        """

        # Determine which validation function to use
        if key_allowed and record_allowed:
            guard_func = is_key_or_record
        elif key_allowed:
            guard_func = is_key
        elif record_allowed:
            guard_func = is_record
        else:
            guard_func = lambda: False

        if none_allowed:
            validate_func = lambda x: x is None or guard_func(x)
        else:
            validate_func = guard_func

        # Check that the input list consists of only None, records, or keys
        invalid_inputs = [x for x in inputs if not validate_func(x)]

        if len(invalid_inputs) > 0:
            caller_name = sys._getframe(1).f_code.co_name
            invalid_inputs_str = "\n".join(str(x) for x in invalid_inputs)

            allowed_values = []
            if key_allowed:
                allowed_values += "Key"
            if record_allowed:
                allowed_values += "Record"
            if none_allowed:
                allowed_values += "None"

            raise RuntimeError(
                f"Inputs of {caller_name} method includes\n"
                f"the following items that are not allowed:\n{invalid_inputs_str}\n"
                f"Allowed values: {', '.join(allowed_values)}."
            )

    @classmethod
    def _group_inputs_by_table(cls, inputs: Sequence[TRecord | TKey | None]) -> dict[str, list]:
        """Group inputs by table. None are allowed, but will be skipped during grouping."""

        inputs_grouped_by_table = defaultdict(list)
        consume(inputs_grouped_by_table[x.get_table()].append(x) for x in inputs if x is not None)
        return inputs_grouped_by_table
