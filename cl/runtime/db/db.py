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

from __future__ import annotations
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Iterable
from typing import Type
from cl.runtime import KeyUtil
from cl.runtime.contexts.env_util import EnvUtil
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.db_key import DbKey
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import PrimitiveType
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import get_primitive_type_names
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_record
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.context_settings import ContextSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin[DbKey], ABC):
    """Polymorphic data storage with dataset isolation."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id)

    def load_one(
        self,
        record_type: Type[TRecord],
        record_or_key: KeyProtocol | PrimitiveType,
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
            result = self.load_one_or_none(record_type, record_or_key, dataset=dataset)
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

    def load_one_or_none(
        self,
        record_type: Type[TRecord],
        record_or_key: KeyProtocol | PrimitiveType | None,
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
        if record_or_key is None:
            # Return None if argument is None
            return None
        elif is_record(record_or_key):
            # Argument is Record, return after checking type
            TypeUtil.check_subtype(record_or_key, record_type)
            return record_or_key  # noqa
        else:
            # Same as is_key but a little faster, can use here because we already know it is not a record
            key_type = record_or_key.get_key_type()
            if is_primitive(record_or_key):
                # Convert to key if primitive type
                key = key_type(record_or_key)
            elif is_key(record_or_key):
                # Check that key object has the right class, subclasses not permitted
                TypeUtil.check_type(record_or_key, key_type, name="record_or_key")
                key = record_or_key
            else:
                raise RuntimeError(
                    f"Parameter 'record_or_key' has type {TypeUtil.name(record_or_key)} which is\n"
                    f"neither a record, nor a key, nor a supported primitive type from the following list:\n"
                    f"{', '.join(get_primitive_type_names())}"
                )

            # Try to retrieve using _load_one_or_none method implemented in derived types
            if (result := self._load_one_or_none(key, dataset=dataset)) is not None:
                TypeUtil.check_subtype(result, record_type)
                return result
            else:
                return None

    @abstractmethod
    def _load_one_or_none(
        self,
        key: KeyProtocol,
        *,
        dataset: str | None = None,
    ) -> RecordProtocol | None:
        """
        Load a single record using a key. The key is already checked not to be None and to have the correct type,
        subclasses are not allowed. Return None if the record is not found in DB.

        Args:
            key: Key object can be expected to have the exact key type, subclasses are not allowed
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

    @abstractmethod
    def load_many(
        self,
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

    @abstractmethod
    def load_all(
        self,
        record_type: Type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load all records of the specified type and its subtypes (excludes other types in the same DB table).

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

    @abstractmethod
    def load_filter(
        self,
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

    @abstractmethod
    def save_one(
        self,
        record: RecordProtocol | None,
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Save records to storage.

        Args:
            record: Record or None.
            dataset: Target dataset as a delimited string, list of levels, or None
        """

    @abstractmethod
    def save_many(
        self,
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

    @abstractmethod
    def delete_one(
        self,
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

    @abstractmethod
    def delete_many(
        self,
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

    @abstractmethod
    def delete_all_and_drop_db(self) -> None:
        """
        IMPORTANT: !!! DESTRUCTIVE - THIS WILL PERMANENTLY DELETE ALL RECORDS WITHOUT THE POSSIBILITY OF RECOVERY

        Notes:
            This method will not run unless both db_id and database start with 'temp_db_prefix'
            specified using Dynaconf and stored in 'DbSettings' class
        """

    @abstractmethod
    def close_connection(self) -> None:
        """Close database connection to releasing resource locks."""

    @classmethod
    @abstractmethod
    def check_db_id(cls, db_id: str) -> None:
        """Check that db_id follows MongoDB database name restrictions, error message otherwise."""

    @classmethod
    def _get_test_db_name(cls) -> str:  # TODO: Use fixture instead
        """Get SQLite database with name based on test namespace."""
        if ProcessContext.is_testing():
            result = f"temp;{ProcessContext.get_env_name().replace('.', ';')}"
            return result
        else:
            raise RuntimeError("Attempting to get test DB name outside a test.")

    @classmethod
    def create(cls, *, db_type: Type | None = None, db_id: str | None = None):
        """Create DB of the specified type, or use DB type from context settings if not specified."""

        # Get DB type from context settings if not specified
        if db_type is None:
            context_settings = ContextSettings.instance()
            db_type = ClassInfo.get_class_type(context_settings.db_class)

        # Get DB identifier if not specified
        if db_id is None:
            env_name = EnvUtil.get_env_name()
            db_id = env_name.replace(".", ";")

        # Create and return a new DB instance
        result = db_type(db_id=db_id)
        return result

    @classmethod
    def error_if_not_temp_db(cls, db_id_or_database_name: str) -> None:
        """Confirm that database id or database name matches temp_db_prefix, error otherwise."""
        context_settings = ContextSettings.instance()
        temp_db_prefix = context_settings.db_temp_prefix
        if not db_id_or_database_name.startswith(temp_db_prefix):
            raise RuntimeError(
                f"Destructive action on database not permitted because db_id or database name "
                f"'{db_id_or_database_name}' does not match temp_db_prefix '{temp_db_prefix}' "
                f"specified in Dynaconf database settings ('DbSettings' class)."
            )
