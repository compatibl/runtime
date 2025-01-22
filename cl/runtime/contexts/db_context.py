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
from typing import Type

import yaml

from cl.runtime import Db
from cl.runtime.contexts.context import Context
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.dataset_util import DatasetUtil
from cl.runtime.db.db_key import DbKey
from cl.runtime.records.for_dataclasses.freezable_util import FreezableUtil
from cl.runtime.records.protocols import TKey, is_record, is_freezable
from cl.runtime.records.protocols import TRecord
from cl.runtime.primitive.format_util import FormatUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.string_serializer import StringSerializer

key_serializer = StringSerializer()
"""Serializer for keys."""

data_serializer = DictSerializer()
"""Serializer for records."""


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
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Db"

    def init(self) -> None:
        """Similar to __init__ but can use fields set after construction."""

        # Initialize from the current context
        if self.db is None:
            self.db = self.get_db()

        # Convert the specified value to string using FormatUtil
        self.dataset = FormatUtil.format_or_none(self.dataset)
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
    def get_db(cls) -> Db:
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
        record_type: Type[TRecord],
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
        return cls.get_db().load_one(
            record_type,
            record_or_key,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def load_one_or_none(
        cls,
        record_type: Type[TRecord],
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
        return cls.get_db().load_one_or_none(
            record_type,
            record_or_key,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def load_many(
        cls,
        record_type: Type[TRecord],
        records_or_keys: Iterable[TRecord | KeyProtocol | tuple | str | None] | None,
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls.get_db().load_many(
            record_type,
            records_or_keys,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def load_all(
        cls,
        record_type: Type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load all records of the specified type and its subtypes (excludes other types in the same DB table).

        Args:
            record_type: Type of the records to load
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """
        return cls.get_db().load_all(  # noqa
            record_type,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def load_filter(
        cls,
        record_type: Type[TRecord],
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
        return cls.get_db().load_filter(  # noqa
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
        cls.get_db().save_one(  # noqa
            record,
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
        # Perform pre-save check
        [cls._pre_save_check(record) for record in records]

        # Invoke DB method with combined dataset
        cls.get_db().save_many(  # noqa
            records,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def delete_one(
        cls,
        key_type: Type[TKey],
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
        cls.get_db().delete_one(  # noqa
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
        cls.get_db().delete_many(  # noqa
            keys,
            dataset=cls.get_dataset(dataset),
        )

    @classmethod
    def _pre_save_check(cls, record: RecordProtocol) -> None:
        if record is None:
            # Confirm argument is not None
            raise RuntimeError("Attempting to save an object with the value of None.")
        elif not is_record(record):
            # Confirm the argument is a record
            raise RuntimeError(f"Attempting to save {type(record).__name__} which is not a record.")
        elif is_freezable(record) and not FreezableUtil.is_frozen(record):  # TODO: Do not allow non-freezable
            raise RuntimeError(f"Record of type {TypeUtil.name(record)} with key {record.get_key()}\n"
                               f"is not frozen before saving, call 'build' or 'freeze' first.")
        else:
            # TODO: To prevent calling get_key more than once, pass to DB save method
            if not key_serializer.serialize_key(record.get_key()):
                record_data = data_serializer.serialize_data(record)
                record_data_str = yaml.dump(record_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
                raise RuntimeError(f"Attempting to save a record with empty key, invoke build before saving.\n"
                                   f"Values of other fields:\n{record_data_str}")
