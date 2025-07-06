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
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.settings.db_settings import DbSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin[DbKey], ABC):
    """Polymorphic data storage with dataset isolation."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

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
    def load_all(
        self,
        table: str,
        record_type: type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        """
        Load all records of the specified type and its subtypes (excludes other types in the same DB table).

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            record_type: Record type to load, error if the result is not this type or its subclass
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
        """

    @abstractmethod
    def load_where(
        self,
        conditions: TRecord,
        *,
        dataset: str | None = None,
    ) -> Sequence[TRecord]:
        """
        Load records that match the argument type or subtype and its specified fields.

        Notes:
            - Only the records that match the argument type or subtype will be returned
            - Specified (not None) fields of the argument are matched using the equality operand
            - Unspecified (None) fields of the argument are ignored
            - Leaving required fields of the argument empty will not cause an error

        Args:
            conditions: Returned records will match the argument type or subtype and its specified (not None) fields
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
    def drop_temp_db(self) -> None:
        """
        IMPORTANT: DESTRUCTIVE - THIS WILL PERMANENTLY DELETE ALL RECORDS WITHOUT THE POSSIBILITY OF RECOVERY

        Notes:
            This method will not run unless db_id starts with the db_temp_prefix specified in settings.yaml.
            The default prefix is 'temp_'.
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
            db_type = TypeInfoCache.get_class_from_type_name(db_settings.db_type)

        # Get DB identifier if not specified
        if db_id is None:
            if not ProcessContext.is_testing():
                db_id = db_settings.db_id
            else:
                raise RuntimeError("Use pytest fixtures to create temporary DBs inside tests.")

        # Create and return a new DB instance
        result = db_type(db_id=db_id)
        return result

    def error_if_not_temp_db(self) -> None:
        """Error if db_id does not start from the db_temp_prefix specified in settings.yaml (defaults to 'temp_')."""
        db_settings = DbSettings.instance()
        if not self.db_id.startswith(db_settings.db_temp_prefix):
            raise RuntimeError(
                f"To drop a DB from code, its name must start from the following prefix: '{db_settings.db_temp_prefix}'\n"
                f"Database name: {self.db_id}"
            )
