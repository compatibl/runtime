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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_type_binding import RecordTypeBinding
from cl.runtime.records.record_type_binding_key import RecordTypeBindingKey
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.server.env import Env
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.env_settings import EnvSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin, ABC):
    """Polymorphic data storage with dataset isolation."""

    _tenant: str = EnvSettings.instance().env_tenant
    """Unique tenant identifier, tenants are isolated when sharing the same DB."""

    _record_type_name_cache: dict[str, set] | None = None
    """Dict of record type name sets for each dataset."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    @abstractmethod
    def load_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder,  # Default value not provided due to the lack of natural default for this method
    ) -> Sequence[RecordMixin]:
        """
        Load records for the specified keys, skipping the records that are not found.

        Args:
            key_type: Key type determines the database table
            keys: Sequence of keys, type(key) must match the key_type argument for each key
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """

    @abstractmethod
    def load_all(
        self,
        key_type: type[KeyProtocol],
        *,
        dataset: str,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records for the specified key type, sorted by key in the specified sort order.

        Args:
            key_type: Key type determines the database table
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only this type and its subtypes
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

    @abstractmethod
    def load_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only this type and its subtypes
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

    @abstractmethod
    def count_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query.

        Args:
            query: Contains query conditions to match
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            restrict_to: The query will return only this type and its subtypes
        """

    @abstractmethod
    def save_many(
        self,
        key_type: type[KeyProtocol],
        records: Sequence[RecordProtocol],
        *,
        dataset: str,
    ) -> None:
        """
        Save multiple records, all of which must have the specified key type.

        Args:
            key_type: Key type determines the database table
            records: Sequence of records to save, record.get_key_type() must match the key_type argument for each record
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
        """

    @abstractmethod
    def delete_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
    ) -> None:
        """
        Delete multiple records, all of which must have the specified key type.

        Args:
            key_type: Key type determines the database table
            keys: Sequence of keys to delete, type(key) must match the key_type argument for each key
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
        """

    @abstractmethod
    def drop_test_db(self) -> None:
        """
        Drop a database as part of a unit test.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - The method is invoked from a unit test based on active_or_default(Env).testing
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
        if active_or_default(Env).testing:
            result = f"temp;{QaUtil.get_test_name_from_call_stack().replace('.', ';')}"
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
            db_type = TypeCache.from_type_name(db_settings.db_type)

        # Get DB identifier if not specified
        if db_id is None:
            if not active_or_default(Env).testing:
                db_id = db_settings.db_id
            else:
                raise RuntimeError("Use pytest fixtures to create temporary DBs inside tests.")

        # Create and return a new DB instance
        result = db_type(db_id=db_id)
        return result

    def check_drop_test_db_preconditions(self) -> None:
        """Error if db_id does not start from db_test_prefix specified in settings.yaml (defaults to 'test_')."""
        if not active_or_default(Env).testing:
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

    def _get_record_type_set(self, dataset: str) -> set:
        """Get the set of record types for the specified dataset."""

        if not self._record_type_name_cache:
            self._record_type_name_cache = {}
        if (result := self._record_type_name_cache.get(dataset)) is None:
            # Load from disk if does not exist
            bindings = self.load_all(RecordTypeBindingKey, cast_to=RecordTypeBinding, dataset=dataset)
            result = {binding.record_type_name for binding in bindings}
            self._record_type_name_cache[dataset] = result
        return result

    def _add_record_type(self, *, record_type: type[RecordProtocol], dataset: str) -> None:
        """Add record type to cache for the specified dataset."""

        if record_type == RecordTypeBinding:
            # Do not register RecordTypeBinding record, as a result it will not be present in REST API
            return

        record_type_name = typename(record_type)
        if record_type_name not in (record_type_name_set := self._get_record_type_set(dataset=dataset)):

            # If the record type is not yet in cache, add parent types to DB and cache
            parent_type_names = TypeCache.get_parent_type_names(record_type, type_kind=TypeKind.RECORD)
            bindings = tuple(
                RecordTypeBinding(
                    record_type_name=parent_type_name,
                    key_type_name=typename(record_type.get_key_type()),
                ).build()
                for parent_type_name in parent_type_names
            )

            # Save bindings to the dataset, it is faster to write all than determine which records are already present
            self.save_many(RecordTypeBindingKey, bindings, dataset=dataset)

            # Add to cache
            record_type_name_set.add(parent_type_names)

    @classmethod
    def _check_dataset(cls, dataset: str) -> None:
        """Error if dataset is None, an empty string, or has invalid format."""
        if dataset is None:
            raise RuntimeError(f"Dataset identifier cannot be None.")
        elif dataset == "":
            raise RuntimeError(f"Dataset identifier cannot be an empty string.")
        elif not isinstance(dataset, str):
            raise RuntimeError(f"Dataset identifier must be a string.")
