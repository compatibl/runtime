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

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable
from typing import Sequence
from more_itertools import consume
from cl.runtime import Db
from cl.runtime import KeyUtil
from cl.runtime.contexts.context import Context
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_singleton_key
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.table_binding_key import TableBindingKey
from cl.runtime.records.table_binding_query import TableBindingQuery
from cl.runtime.records.type_query import TypeQuery
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in cache lookup."""


@dataclass(slots=True, kw_only=True)
class DbContext(Context):
    """Includes database and dataset."""

    db: Db | None = None
    """Database of the storage context."""

    dataset: str | None = None
    """
    Dataset can be a single token or multiple tokens in backslash-delimited format.

    Notes:
      - Datasets for the DbContext stack are concatenated in the order entered separately for each DB
      - Because 'with' clause cannot be under if/else, in some cases dataset may be None
        but 'with DbContext(...)' clause would still be present.
      - If dataset is None, it is is disregarded
      - If dataset is None for the entire the DbContext stack, this method returns None
    """

    @classmethod
    def get_base_type(cls) -> type:
        return DbContext

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Initialize from the current context
        if self.db is None:
            self.db = self._get_db()

        # TODO: !!! Currently, only the latest context is reproduced in celery workers
        #       This may cause problems with the current design and has to be reviewed
        # Get previous dataset value from the latest context in context stack that has the same DB
        reversed_stack = reversed(self.get_context_stack())
        # Set to root dataset if no previous contexts with the same DB are found in context stack
        previous_dataset = next(
            (context.dataset for context in reversed_stack if context.db.db_id == self.db.db_id), DatasetUtil.root()
        )

        if self.dataset:
            # If specified for this instance, combine with previous using backslash separator
            self.dataset = f"{previous_dataset}\\{self.dataset}"
        else:
            # Otherwise use previous
            self.dataset = previous_dataset

        #  Load 'db' field of this context using 'Context.current()'
        if self.db is not None and is_key(self.db):
            self.db = DbContext.load_one(self.db)  # TODO: Revise to use DB settings

    @classmethod
    def get_db_id(cls) -> str:
        """Get db_id of the database from the current context or error message if not inside 'with DbContext(...)' clause."""
        return cls._get_db().db_id

    @classmethod
    def get_dataset(cls, dataset: str | None = None) -> str | None:
        """
        Unique dataset in backslash-delimited format obtained by concatenating identifiers from the DbContext stack
        for the same DB as the current context in the order entered, or None outside 'with DbContext(...)' clause.
        The result is combined with dataset. If the overall result is None, root dataset is used.
        """
        if (context := cls.current_or_none()) is not None:
            # Use the value from the current context if not None
            return context.dataset
        else:
            # Otherwise return root dataset
            return DatasetUtil.root()

    @classmethod
    def get_bindings(cls) -> tuple[TableBinding, ...]:
        """
        Return table bindings to key type in alphabetical order of table name, then key type name.
        
        Notes:
            More than one table can exist for the same key type.
        """
        query = TableBindingQuery().build()
        bindings = cls.load_where(query, cast_to=TableBinding)
        return bindings

    @classmethod
    def get_bound_tables(cls, *, key_type: type[KeyMixin]) -> tuple[str, ...]:
        """
        Return tables for the specified key type in alphabetical order.
        
        Returns:
            Table names in non-delimited PascalCase format.
        
        Args:
            key_type: Key type name for which the tables are returned.
        """
        query = TableBindingQuery(key_type=TypeUtil.name(key_type)).build()
        bindings = cls.load_where(query, cast_to=TableBinding)
        result = tuple(binding.table for binding in bindings)
        return result

    @classmethod
    def get_bound_type(cls, *, table: str) -> type[KeyMixin]:
        """
        Return key type for the specified table name.

        Args:
            table: Table name in non-delimited PascalCase format.
        """
        key = TableBindingKey(table=table).build()
        binding = cls.load_one(key)
        result = TypeInfoCache.get_class_from_type_name(binding.key_type)
        return result

    @classmethod
    def load_one(
        cls,
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
            result = cls.load_one_or_none(record_or_key, dataset=dataset, cast_to=cast_to)
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

    @classmethod
    def load_one_or_none(
        cls,
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

        result = cls.load_many([record_or_key], dataset=dataset, cast_to=cast_to)
        if len(result) == 1:
            return result[0]
        else:
            raise RuntimeError("DbContext.load_many returned more records than requested.")

    @classmethod
    def load_many(
        cls,
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
        invalid_inputs = [x for x in records_or_keys if x is not None and not is_key_or_record(x)]
        if len(invalid_inputs) > 0:
            invalid_inputs_str = "\n".join(str(x) for x in invalid_inputs)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following items that are not record, key or None:\n{invalid_inputs_str}"
            )

        # Perform these checks if cast_to is specified
        if cast_to is not None:
            # Check that the keys in the input list have the same type as cast_to.get_key_type()
            key_type = cast_to.get_key_type()
            invalid_keys = [x for x in records_or_keys if is_key(x) and not isinstance(x, key_type)]
            if len(invalid_keys) > 0:
                invalid_keys_str = "\n".join(str(x) for x in invalid_keys)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DbContext includes the following keys\n"
                    f"whose type is not the same as the key type {TypeUtil.name(key_type)}\n"
                    f"of the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_keys_str}"
                )
            # Check that the records in the input list are derived from cast_to
            invalid_records = [x for x in records_or_keys if is_record(x) and not isinstance(x, cast_to)]
            if len(invalid_records) > 0:
                invalid_records_str = "\n".join(str(x) for x in invalid_records)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DbContext includes the following records\n"
                    f"that are not derived from the cast_to parameter {TypeUtil.name(cast_to)}:\n{invalid_records_str}"
                )

        # Check that all records or keys in object format are frozen
        unfrozen_inputs = [x for x in records_or_keys if x is not None and not x.is_frozen()]
        if len(unfrozen_inputs) > 0:
            unfrozen_inputs_str = "\n".join(str(x) for x in unfrozen_inputs)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following items that are not frozen:\n{unfrozen_inputs_str}"
            )

        # The list of keys to load, skip None and records
        keys_to_load = [x for x in records_or_keys if is_key(x)]

        # Group keys by table
        keys_to_load_grouped_by_table = defaultdict(list)
        consume(keys_to_load_grouped_by_table[key.get_table()].append(key) for key in keys_to_load)

        # Get records from DB, the result is unsorted and grouped by table
        loaded_records_grouped_by_table = [
            cls._get_db().load_many_unsorted(table, table_keys, dataset=dataset)
            for table, table_keys in keys_to_load_grouped_by_table.items()
        ]

        # Concatenated list
        loaded_records = [item for sublist in loaded_records_grouped_by_table for item in sublist]
        normalized_loaded_keys = [KeyUtil.normalize_key(x.serialize_key()) for x in loaded_records]

        # Create a dictionary with pairs consisting of serialized key (after normalization) and the record for this key
        loaded_records_dict = {k: v for k, v in zip(normalized_loaded_keys, loaded_records)}

        # Populate the result with records loaded using input keys, pass through None and input records
        result = tuple(
            loaded_records_dict.get(KeyUtil.normalize_key(x.serialize_key()), None) if is_key(x) else x
            for x in records_or_keys
        )

        # Cast to cast_to if specified
        if cast_to is not None:
            result = tuple(CastUtil.cast(cast_to, x) for x in result)
        return result

    @classmethod
    def load_where(
        cls,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        slice_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            slice_to: Slice fields from the stored record using projection to return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        result = cls._get_db().load_where(
            query,
            dataset=cls.get_dataset(dataset),
            cast_to=cast_to,
            filter_to=filter_to,
            slice_to=slice_to,
            limit=limit,
            skip=skip,
        )
        return result

    @classmethod
    def load_type(
        cls,
        target_type: type[TKey],
        *,
        dataset: str | None = None,
        cast_to: type[TKey] | None = None,
        slice_to: type[TKey] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TKey]:
        """
        Load all records of target_type and its subtypes.

        Notes:
            Error if target_type defines custom tables by overriding get_table, use load_where in this case.

        Args:
            target_type: The query will return only the subtypes of this type (defaults to the query target type)
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            slice_to: Slice fields from the stored record using projection to return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        query = TypeQuery(target_type).build()
        result = cls._get_db().load_where(
            query,
            dataset=cls.get_dataset(dataset),
            cast_to=cast_to,
            slice_to=slice_to,
            limit=limit,
            skip=skip,
        )
        return result

    @classmethod
    def count_where(
        cls,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        filter_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query using the current context's DB.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            filter_to: Count only the subtypes of this type (defaults to the query target type)
        """
        db = cls._get_db()
        return db.count_where(query, dataset=dataset, filter_to=filter_to)

    @classmethod
    def save_one(
        cls,
        record: RecordProtocol,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            record: Record or None.
            dataset: Target dataset as a delimited string, list of levels, or None
        """
        # Perform pre-save check
        cls._pre_save_check(record)

        # Invoke DB method with combined dataset
        cls._get_db().save_many(  # noqa
            [record],
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def save_many(
        cls,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            records: Iterable of records.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        # Convert to list, this must be done first to ensure single traversal of generator
        # TODO: Do this incrementally for a large number of records
        records = list(records)

        # Perform pre-save check for each record
        [cls._pre_save_check(record) for record in records]

        # Invoke save_many method of DB implementation
        cls._get_db().save_many(  # noqa
            records,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def delete_one(
        cls,
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete one record for the specified key type using its key in one of several possible formats.

        Args:
            key: Key in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls.delete_many([key], dataset=dataset)

    @classmethod
    def delete_many(
        cls,
        keys: Sequence[TKey | None] | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

        Args:
            keys: Sequence of keys to delete.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

        if not keys:
            return

        # Check that the input list consists of only None or keys
        invalid_inputs = [x for x in keys if x is not None and not is_key(x)]
        if len(invalid_inputs) > 0:
            invalid_inputs_str = "\n".join(str(x) for x in invalid_inputs)
            raise RuntimeError(
                f"Parameter 'keys' of delete_many method includes\n"
                f"the following items that are not key or None:\n{invalid_inputs_str}"
            )

        # Group keys by table
        keys_to_delete_grouped_by_table = defaultdict(list)
        consume(keys_to_delete_grouped_by_table[key.get_table()].append(key) for key in keys)

        # Perform delete for each table
        consume(
            cls._get_db().delete_many(table, table_keys, dataset=dataset)
            for table, table_keys in keys_to_delete_grouped_by_table.items()
        )

    @classmethod
    def drop_temp_db(cls) -> None:
        """
        IMPORTANT: DESTRUCTIVE - THIS WILL PERMANENTLY DELETE ALL RECORDS WITHOUT THE POSSIBILITY OF RECOVERY

        Notes:
            This method will not run unless db_id starts with the db_temp_prefix specified in settings.yaml.
            The default prefix is 'temp_'.
        """
        cls._get_db().drop_temp_db()

    @classmethod
    def _get_db(cls) -> Db:
        """
        Return DB for the current DbContext inside the 'with DbContext(...)' clause.
        Return the default DB from settings outside the outermost 'with DbContext(...)' clause.
        """
        if (db_context := DbContext.current_or_none()) is not None:
            # Use the value from the current context if not None
            return db_context.db
        else:
            if ProcessContext.is_testing():
                raise RuntimeError(
                    "To use DB in a test, specify pytest_default_db or similar pytest fixture or "
                    "use 'with DbContext(...)' clause if not using pytest."
                )
            else:
                raise RuntimeError("Attempting to access DB outside the outermost 'with DbContext(...)' clause.")

    @classmethod
    def _pre_save_check(cls, record: RecordProtocol) -> None:
        if record is None:
            # Confirm argument is not None
            raise RuntimeError("Record passed to DB save method is None.")
        elif not is_record(record):
            # Confirm the argument is a record
            raise RuntimeError(f"Attempting to an object of {type(record).__name__} which is not a record.")
        elif not record.is_frozen():
            raise RuntimeError(
                f"Build method not invoked before saving for an record of type\n"
                f"{TypeUtil.name(record)} with key {record.get_key()}\n"
            )
        else:
            # TODO: To prevent calling get_key more than once, pass to DB save method
            if not KeySerializers.DELIMITED.serialize(key := record.get_key()):
                # Error only if not a singleton
                if not is_singleton_key(key):
                    record_data_str = BootstrapSerializers.YAML.serialize(record)
                    raise RuntimeError(
                        f"Attempting to save a record with empty key, invoke build before saving.\n"
                        f"Values of other fields:\n{record_data_str}"
                    )
