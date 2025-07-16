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
from typing import Iterable
from typing import Sequence
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.db.db_key import DbKey
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.table_binding_key import TableBindingKey
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.settings.db_settings import DbSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin, ABC):
    """Polymorphic data storage with dataset isolation."""

    _table_binding_cache: dict[str, TableBinding] = required(default_factory=lambda: {})
    """Cache of table bindings for the DB."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    @abstractmethod
    def load_table(
        self,
        table: str,
        *,
        dataset: str | None = None,
        cast_to: type[TRecord] | None = None,
        filter_to: type[TRecord] | None = None,
        slice_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord]:
        """
        Load all records from the specified table.

        Args:
            table: The table from which the records are loaded
            dataset: Backslash-delimited dataset is combined with root dataset of the DB
            cast_to: Cast the result to this type (error if not a subtype)
            filter_to: The query will return only the subtypes of this type (defaults to the query target type)
            slice_to: Slice fields from the stored record using projection to return instances of this type
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
    def delete_many(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> None:
        """
        Delete records using an iterable of keys.

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

    def _add_binding(
        self,
        *,
        table: str,
        key_type: type[KeyMixin],
        ) -> None:
        """
        Add a new table, or if the table already exists, verify that the key type is the same.

        Args:
            table: Table name in non-delimited PascalCase format
            key_type: Key type of the table (must implement KeyProtocol)
        """
        if (table_binding := self._table_binding_cache.get(table)) is None:
            # Attempt to load from DB
            table_binding_key = TableBindingKey(table=table).build()
            load_result = self.load_many_unsorted(table, [table_binding_key])
            if load_result:
                # Update cache
                table_binding = CastUtil.cast(TableBinding, load_result[0])
                self._table_binding_cache[table] = table_binding

        if table_binding is None:
            # Add to DB and cache
            table_binding = TableBinding(table=table, key_type=TypeUtil.name(key_type))
            self._table_binding_cache[table] = table_binding
            self.save_many([table_binding])
        else:
            # Verify that the key type is the same
            if table_binding.key_type != (key_type_str := TypeUtil.name(key_type)):
                raise RuntimeError(
                    f"Binding for table {table} cannot be created for key type {key_type_str}\n"
                    f"because it already exists with a different key type: {table_binding.key_type}")

    def check_drop_test_db_preconditions(self) -> None:
        """Error if db_id does not start from db_test_prefix specified in settings.yaml (defaults to 'test_')."""
        if not ProcessContext.is_testing():
            raise RuntimeError(f"Cannot drop a unit test DB when not invoked from a running unit test.")

        db_settings = DbSettings.instance()
        if not self.db_id.startswith(db_settings.db_test_prefix):
            raise RuntimeError(
                f"Cannot drop a unit test DB from code because its db_id={self.db_id}\n"
                f"does not start from unit test DB prefix '{db_settings.db_test_prefix}'.")

    def check_drop_temp_db_preconditions(self, *, user_approval: bool) -> None:
        """
        Check user approval and raise an error if db_id does not start from db_temp_prefix
        specified in settings.yaml (defaults to 'temp_').
        """
        if not user_approval:
            raise RuntimeError(
                f"Cannot drop a temporary DB from code without explicit user approval.")

        db_settings = DbSettings.instance()
        if not self.db_id.startswith(db_settings.db_temp_prefix):
            raise RuntimeError(
                f"Cannot drop a DB from code even with user approval because its db_id={self.db_id}\n"
                f"does not start from temporary DB prefix '{db_settings.db_temp_prefix}'.")
