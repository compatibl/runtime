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

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Self
from typing import Sequence
from typing import cast
from more_itertools import consume
from cl.runtime import Db
from cl.runtime import TypeCache
from cl.runtime.db.data_source_key import DataSourceKey
from cl.runtime.db.dataset import Dataset
from cl.runtime.db.dataset_key import DatasetKey
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.resource_key import ResourceKey
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.table_binding_key import TableBindingKey
from cl.runtime.records.table_binding_key_query_by_table import TableBindingKeyQueryByTable
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.key_serializers import KeySerializers

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class DataSource(DataSourceKey, RecordMixin):
    """Rules for hierarchical lookup in multiple databases and datasets with data access control."""

    db: DbKey = required()
    """Database where lookup is performed (initialized to DB from the current context if not specified)."""

    dataset: DatasetKey = required()
    """Dataset within the database (initialized to the dataset from the current context if not specified)."""

    parent: DataSourceKey | None = None
    """Search in parent if not found in self, default data source is always added as ultimate parent (optional)."""

    included: list[ResourceKey] | None = None
    """Lookup here only the resources on this list, continue to parent for all other resources (optional)."""

    excluded: list[ResourceKey] | None = None
    """Continue to parent without lookup here for resources in this list (optional)."""

    designated: list[ResourceKey] | None = None
    """Lookup these resources only here, not in any child or parent (optional)."""

    def get_key(self) -> DataSourceKey:
        return DataSourceKey(data_source_id=self.data_source_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Load the database object, use default DB if not specified
        if self.db is None:
            self.db = Db.create()  # TODO: Move initialization code here?
        elif is_key(self.db):
            self.db = self.load_one(self.db)

        _LOGGER.info(f"Connected to DB type '{TypeUtil.name(self.db)}', db_id = '{self.db.db_id}'.")

        # Load dataset, use root dataset if not specified
        if self.dataset is None:
            self.dataset = Dataset.get_root()

        # TODO: These features are not yet supported
        if self.parent is not None:
            raise RuntimeError("DataSource.parent is not yet supported.")
        if self.included is not None:
            raise RuntimeError("DataSource.included is not yet supported.")
        if self.excluded is not None:
            raise RuntimeError("DataSource.excluded is not yet supported.")
        if self.designated is not None:
            raise RuntimeError("DataSource.designated is not yet supported.")

    def get_bindings(self) -> tuple[TableBinding, ...]:
        """Return table to record type bindings in alphabetical order of table name followed by record type name."""

        # Load from DB as cache may be out of date
        bindings = self.load_type(TableBinding)
        # Sort bindings by table name first and then by record type in alphabetical order
        return tuple(sorted(bindings, key=lambda x: (x.table, x.record_type)))

    def get_tables(self) -> tuple[str, ...]:
        """Return DB table names in alphabetical order of PascalCase format."""

        # Load from DB as cache may be out of date
        bindings = self.load_type(TableBinding)
        # Convert to set to remove duplicates, sort in alphabetical order, convert back to tuple
        return tuple(sorted(set(binding.table for binding in bindings)))

    def get_table(self, *, record_type_name: str) -> str:
        """Return DB table name for the specified record type name, error if the record type is not stored."""

        # Load from DB as cache may be out of date
        binding = self.load_one_or_none(TableBindingKey(record_type_name=record_type_name))
        if binding:
            return binding.table
        else:
            raise RuntimeError(f"Records of type {record_type_name} not found.")

    def get_key_type_name(self, *, table: str) -> str:
        """
        Return PascalCase key type name for the specified table name.

        Args:
            table: Table name in PascalCase format (optional, filter by table if specified).
        """

        # Load from DB as cache may be out of date
        query = TableBindingKeyQueryByTable(table=table).build()
        bindings = self.load_where(query, cast_to=TableBinding)

        # Eliminate duplicates
        key_type_names = tuple(set(binding.key_type for binding in bindings))

        if len(key_type_names) == 1:
            return key_type_names[0]
        elif len(key_type_names) == 0:
            raise RuntimeError(f"No records found for table {table}.")
        else:
            raise RuntimeError(f"Multiple key types found for table {table}.")

        # Sort in alphabetical order of record_type (not the same as query sort order) and convert to tuple
        return tuple(sorted(binding.record_type for binding in bindings))

    def get_record_type_names(self, *, table: str | None = None) -> tuple[str, ...]:
        """
        Return PascalCase record type names in alphabetical order for records stored in this DB,
        with optional filtering by table name.

        Returns:
            Tuple of PascalCase record type names in alphabetical order or an empty tuple.

        Args:
            table: Table name in PascalCase format (optional, filter by table if specified).
        """

        # Load from DB as cache may be out of date
        query = TableBindingKeyQueryByTable(table=table).build()
        bindings = self.load_where(query, cast_to=TableBinding)

        # Sort in alphabetical order of record_type (not the same as query sort order) and convert to tuple
        return tuple(sorted(binding.record_type for binding in bindings))

    def get_common_base_record_type_name(self, *, table: str) -> str:
        """
        Return the name of the common type for all records stored in this table, error if the table is empty.

        Args:
            table: Table name in PascalCase format (required).
        """
        
        if not table:
            raise RuntimeError("Table name is required in get_common_base_record_type_name method.")

        # Get record type names stored in this table
        bound_type_names = self.get_record_type_names(table=table)
        
        if bound_type_names:
            # Find the common base name
            result = TypeCache.get_common_base_record_type_name(
                types_or_names=bound_type_names,
                type_kind=TypeKind.RECORD,
            )
            return result
        else:
            # The case of empty bound_type_names can only occur if table name is stale because bindings
            # will include at least one record type when data is added, raise an error
            raise RuntimeError(f"Table {table} is empty.")

    def load_one(
        self,
        record_or_key: TKey,
        *,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """

        # TODO: This is a temporary safeguard, remove after verification
        if isinstance(record_or_key, type):
            raise RuntimeError("Code update error for load_one signature.")

        if record_or_key is not None:
            result = self.load_one_or_none(record_or_key, cast_to=cast_to)
            if result is None:
                key_str = KeySerializers.DELIMITED.serialize(record_or_key.get_key())
                cast_to_str = f"\nwhen loading type {TypeUtil.name(cast_to)}" if cast_to else ""
                raise RuntimeError(
                    f"Record not found for key {key_str}{cast_to_str}.\n"
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
        cast_to: type[TRecord] | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """

        # TODO: This is a temporary safeguard, remove after verification
        if isinstance(record_or_key, type):
            raise RuntimeError("Code update error for load_one_or_none signature.")

        result = self.load_many([record_or_key], cast_to=cast_to)
        if len(result) == 1:
            return result[0]
        else:
            raise RuntimeError("active(DataSource).load_many returned more records than requested.")

    def load_many(
        self,
        records_or_keys: Sequence[TRecord | TKey | None] | None,
        *,
        sort_order: SortOrder = SortOrder.INPUT,
        cast_to: type[TRecord] | None = None,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            sort_order: Sort in the order of 'records_or_keys' parameter for INPUT (default), or as specified
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
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following keys\n"
                    f"whose type is not the same as the key type {TypeUtil.name(key_type)}\n"
                    f"of the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_keys_str}"
                )
            # Check that the records in the input list are derived from cast_to
            invalid_records = [x for x in records_or_keys if is_record(x) and not isinstance(x, cast_to)]
            if len(invalid_records) > 0:
                invalid_records_str = "\n".join(str(x) for x in invalid_records)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following records\n"
                    f"that are not derived from the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_records_str}"
                )

        # Check that all records or keys in object format are frozen
        self._check_frozen_inputs(records_or_keys)

        # The list of keys to load, skip None and records
        keys_to_load = [x for x in records_or_keys if is_key(x)]

        # Group keys by table
        keys_to_load_grouped_by_key_type = self._group_inputs_by_key_type(keys_to_load)

        # Get records from DB, the result is unsorted and grouped by table
        loaded_records_grouped_by_key_type = [
            self._get_db().load_many(key_type, keys_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, keys_for_key_type in keys_to_load_grouped_by_key_type.items()
        ]

        # Concatenated list
        loaded_records = [item for sublist in loaded_records_grouped_by_key_type for item in sublist]
        serialized_loaded_keys = [KeySerializers.TUPLE.serialize(x.get_key()) for x in loaded_records]

        # Create a dictionary with pairs consisting of serialized key (after normalization) and the record for this key
        loaded_records_dict = {k: v for k, v in zip(serialized_loaded_keys, loaded_records)}

        # Populate the result with records loaded using input keys, pass through None and input records
        result = tuple(
            loaded_records_dict.get(KeySerializers.TUPLE.serialize(x), None) if is_key(x) else x
            for x in records_or_keys
        )

        # Cast to cast_to if specified, pass through None
        if cast_to is not None:
            result = tuple(CastUtil.cast_or_none(cast_to, x) for x in result)
        return result

    def load_type(
        self,
        restrict_to: type[TRecord],
        *,
        sort_order: SortOrder = SortOrder.ASC,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records of 'restrict_to' type and its subtypes from all tables where they are stored.

        Args:
            restrict_to: The query will return only this type and its subtypes
            sort_order: Sort in the specified order for each key field, defaults to ASC for this method
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        # Load table for the key type of 'restrict_to' parameter
        return self._get_db().load_all(
            restrict_to.get_key_type(),
            dataset=self.dataset.dataset_id,
            sort_order=sort_order,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    def load_all(
        self,
        key_type: type[KeyProtocol],
        *,
        sort_order: SortOrder = SortOrder.ASC,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records for the specified key type.

        Args:
            key_type: Key type determines the database table
            sort_order: Sort in the specified order for each key field, defaults to ASC for this method
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return self._get_db().load_all(
            key_type=key_type,
            dataset=self.dataset.dataset_id,
            sort_order=sort_order,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    def load_where(
        self,
        query: QueryMixin,
        *,
        sort_order: SortOrder = SortOrder.ASC,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC in query class
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return self._get_db().load_where(
            query,
            dataset=self.dataset.dataset_id,
            sort_order=sort_order,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    def count_where(
        self,
        query: QueryMixin,
        *,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query using the current context's DB.

        Args:
            query: Contains query conditions to match
            restrict_to: Count only the subtypes of this type (defaults to the query target type)
        """
        return self._get_db().count_where(query, dataset=self.dataset.dataset_id, restrict_to=restrict_to)

    def save_one(
        self,
        record: RecordProtocol,
    ) -> None:
        """Save the specified record to storage, replace rather than update individual fields if it exists."""
        self.save_many([record])

    def save_many(
        self,
        records: Sequence[RecordProtocol],
    ) -> None:
        """Save the specified records to storage, replace rather than update individual fields for those that exist."""

        if not records:
            return

        # Validate inputs. Allowed values are records and None.
        self._check_invalid_inputs(records, key_allowed=False)
        self._check_frozen_inputs(records)

        # Group records by table
        records_grouped_by_key_type = self._group_inputs_by_key_type(records)

        # Save records for each table
        [
            self._get_db().save_many(key_type, records_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, records_for_key_type in records_grouped_by_key_type.items()
        ]

    def delete_one(
        self,
        key: KeyProtocol,
    ) -> None:
        """Delete record for the specified key in object, tuple or string format (no error if not found)."""
        return self.delete_many([key])

    def delete_many(
        self,
        keys: Sequence[KeyProtocol],
    ) -> None:
        """Delete records for the specified keys in object, tuple or string format (no error if not found)."""

        if not keys:
            return

        # Validate inputs. Allowed values are keys and None.
        self._check_invalid_inputs(keys, record_allowed=False)
        self._check_frozen_inputs(keys)

        keys_grouped_by_key_type = self._group_inputs_by_key_type(keys)

        [
            self._get_db().delete_many(key_type, records_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, records_for_key_type in keys_grouped_by_key_type.items()
        ]

    def _get_db(self) -> Db:
        """Cast db key type to record type, the record is already loaded by the __init method."""
        return cast(Db, self.db)

    def _get_parent(self) -> Self:
        """Cast parent key types to record type, the record is already loaded by the __init method."""
        return cast(Self, self.parent)

    @classmethod
    def _check_frozen_inputs(cls, inputs: Sequence[TRecord | TKey | None]) -> None:
        """Check that all records and key params are frozen."""

        unfrozen_input_keys = [x.get_key() for x in inputs if x is not None and not x.is_frozen()]
        if len(unfrozen_input_keys) > 0:
            unfrozen_inputs_str = "\n".join(str(x) for x in unfrozen_input_keys)
            raise RuntimeError(
                f"Data source method arguments include the following items that are not frozen:\n{unfrozen_inputs_str}"
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
        Use flags 'key_allowed', 'record_allowed', and 'none_allowed' to control the list of valid types.
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
        invalid_input_keys = [x.get_key() if x is not None else None for x in inputs if not validate_func(x)]

        if len(invalid_input_keys) > 0:
            invalid_inputs_str = "\n".join(str(x) for x in invalid_input_keys)

            allowed_values = []
            if key_allowed:
                allowed_values += "Key"
            if record_allowed:
                allowed_values += "Record"
            if none_allowed:
                allowed_values += "None"

            raise RuntimeError(
                f"Data source method params include the following invalid arguments:\n{invalid_inputs_str}\n"
                f"Valid argument types: {', '.join(allowed_values)}."
            )

    @classmethod
    def _group_inputs_by_key_type(
            cls,
            inputs: Sequence[TRecord | TKey | None]
        ) -> dict[type[KeyProtocol], Sequence[TRecord | TKey | None]]:
        """Group inputs by key type, skipping sequence elements that are None."""
        result = defaultdict(list)
        consume(result[x.get_key_type()].append(x) for x in inputs if x is not None)
        return result
