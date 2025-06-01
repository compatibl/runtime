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

from dataclasses import dataclass
from typing import Iterable
from typing import Sequence
from cl.runtime import Db
from cl.runtime import KeyUtil
from cl.runtime.contexts.context import Context
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.db.db_key import DbKey
from cl.runtime.records.generic_util import GenericUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_singleton_key
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.type_util import TypeUtil
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
            self.db = DbContext.load_one(DbKey, self.db)  # TODO: Revise to use DB settings

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
    def load_one(
        cls,
        record_type: type[TRecord],
        record_or_key: KeyProtocol | TPrimitive,
        *,
        dataset: str | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        if record_or_key is not None:
            result = cls.load_one_or_none(record_type, record_or_key, dataset=dataset)
            if result is None:
                raise RuntimeError(
                    f"Record not found for key {KeyUtil.format(record_or_key)} when loading type "
                    f"{TypeUtil.name(record_type)}.\n"
                    f"Use 'load_one_or_none' method to return None instead of raising an error."
                )
            return result
        else:
            raise RuntimeError(
                f"Parameter 'record_or_key' is None for load_one method when loading type "
                f"{TypeUtil.name(record_type)}.\n"
                f"Use 'load_one_or_none' method to return None instead of raising an error."
            )

    @classmethod
    def load_one_or_none(
        cls,
        record_type: type[TRecord],
        record_or_key: KeyProtocol | TPrimitive | None,
        *,
        dataset: str | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        result = cls.load_many(record_type, [record_or_key], dataset=dataset)
        if len(result) == 1:
            return result[0]
        else:
            raise RuntimeError("DbContext.load_many returned more records than requested.")

    @classmethod
    def load_many(
        cls,
        record_type: type[TRecord],
        records_or_keys: Sequence[TRecord | TKey | tuple | None] | None,
        *,
        dataset: str | None = None,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

        # Pass through None or an empty sequence
        if not records_or_keys:
            return records_or_keys

        # Check that the input list consists of only None, records, or keys in object or tuple format
        invalid_inputs = [
            x for x in records_or_keys if x is not None and not isinstance(x, tuple) and not is_key_or_record(x)
        ]
        if len(invalid_inputs) > 0:
            invalid_inputs_str = "\n".join(str(x) for x in invalid_inputs)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following items that are not None, key, or record:\n{invalid_inputs_str}"
            )

        # Check that the keys in the input list have type record_type.get_key_type()
        key_type = record_type.get_key_type()
        invalid_keys = [x for x in records_or_keys if is_key(x) and not GenericUtil.is_instance(x, key_type)]
        if len(invalid_keys) > 0:
            invalid_keys_str = "\n".join(str(x) for x in invalid_keys)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following keys whose type is not {TypeUtil.name(key_type)}:\n{invalid_keys_str}"
            )

        # Check that the records in the input list are derived from record_type
        invalid_records = [x for x in records_or_keys if is_record(x) and not isinstance(x, record_type)]
        if len(invalid_records) > 0:
            invalid_records_str = "\n".join(str(x) for x in invalid_records)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following records that are not derived from {TypeUtil.name(record_type)}:\n{invalid_records_str}"
            )

        # Check that all records or keys in object format are frozen
        unfrozen_inputs = [
            x for x in records_or_keys if x is not None and not isinstance(x, tuple) and not x.is_frozen()
        ]
        if len(unfrozen_inputs) > 0:
            unfrozen_inputs_str = "\n".join(str(x) for x in unfrozen_inputs)
            raise RuntimeError(
                f"Parameter 'records_or_keys' of load_many method includes\n"
                f"the following items that are not frozen:\n{unfrozen_inputs_str}"
            )

        # Convert keys to tuple unless already a tuple, pass through all other item types
        tuple_keys_or_records = [
            _KEY_SERIALIZER.serialize(x) if x is not None and is_key(x) else x for x in records_or_keys
        ]

        # Keys only, skip None and records
        queried_tuple_keys = [x for x in tuple_keys_or_records if isinstance(x, tuple)]

        # Get records from DB, the result is unsorted
        queried_records = cls._get_db().load_many_unsorted(record_type, queried_tuple_keys, dataset=dataset)

        # Create a dictionary with pairs consisting of key in tuple format and the record for this key
        queried_records_dict = {_KEY_SERIALIZER.serialize(x.get_key()): x for x in queried_records}

        # Populate the result with records queried using input keys, pass through None and input records
        result = [queried_records_dict.get(x, None) if isinstance(x, tuple) else x for x in tuple_keys_or_records]
        return result

    @classmethod
    def load_all(
        cls,
        record_type: type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load all records of the specified type and its subtypes (excludes other types in the same DB table).

        Args:
            record_type: Type of the records to load
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls._get_db().load_all(  # noqa
            record_type,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def query(
        cls,
        record_type: type[TRecord],
        query: QueryMixin[TRecord],  # TODO: Use QueryProtocol?
        *,
        dataset: str | None = None,
    ) -> Sequence[TRecord]:
        """
        Load all records of the specified type and its subtypes that match the query
        (excludes other types in the same DB table).

        Args:
            record_type: Type of the records to load
            query: Query used to select the records
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls._get_db().query(  # noqa
            record_type,
            query,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def load_filter(
        cls,
        record_type: type[TRecord],
        filter_obj: TRecord,
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord]:
        """
        Load records where values of those fields that are set in the filter match the filter.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            filter_obj: Instance of 'record_type' whose fields are used for the query
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls._get_db().load_filter(  # noqa
            record_type,
            filter_obj,
            dataset=cls.get_dataset(dataset),
        )

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
        key_type: type[TKey],
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete one record for the specified key type using its key in one of several possible formats.

        Args:
            key_type: Key type to delete, used to determine the database table
            key: Key in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        cls._get_db().delete_one(  # noqa
            key_type,
            key,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def delete_many(
        cls,
        keys: Iterable[KeyProtocol] | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

        Args:
            keys: Iterable of keys.
            dataset: Target dataset as a delimited string, list of levels, or None
        """
        cls._get_db().delete_many(  # noqa
            keys,
            dataset=cls.get_dataset(dataset),
        )

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
