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
from typing import Sequence
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.db_key import DbKey
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.settings.context_settings import ContextSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin[DbKey], ABC):
    """Polymorphic data storage with dataset isolation."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    @abstractmethod
    def load_many_unsorted(
        self,
        record_type: type[TRecord],
        keys: Sequence[tuple],
        *,
        dataset: str | None = None,
    ) -> Sequence[TRecord]:
        """
        Load records for the specified sequence of keys in tuple format.
        The result is unsorted and skips the records that are not found.

        Args:
            record_type: Record type to load, error if the result is not this type or its subclass
            keys: A sequence of keys in tuple format without key type
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

    @abstractmethod
    def load_all(
        self,
        record_type: type[TRecord],
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
    def query(
        self,
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

    @abstractmethod
    def load_filter(
        self,
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
            dataset: Dataset as backslash-delimited string
        """

    @abstractmethod
    def delete_one(
        self,
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
    def create(cls, *, db_type: type | None = None, db_id: str | None = None):
        """Create DB of the specified type, or use DB type from context settings if not specified."""

        # Get DB type from context settings if not specified
        if db_type is None:
            context_settings = ContextSettings.instance()
            db_type = TypeInfoCache.get_class_from_qual_name(context_settings.db_class)

        # Get DB identifier if not specified
        if db_id is None:
            env_name = QaUtil.get_env_name()
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
