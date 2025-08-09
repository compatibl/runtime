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
from more_itertools import consume
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.contexts.env import Env
from cl.runtime.db.db_key import DbKey
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.table_binding_key_query_by_table import TableBindingKeyQueryByTable
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.settings.db_settings import DbSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin, ABC):
    """Polymorphic data storage with dataset isolation."""

    _table_binding_cache: dict[str, dict[tuple[str, str], TableBinding]] | None = None
    """Cache of table to record type bindings for records stored in this DB, indexed by dataset and TableBindingKey."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    @abstractmethod
    def load_table(
        self,
        table: str,
        *,
        dataset: str,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records from the specified table.

        Args:
            table: The table from which the records are loaded
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
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
        dataset: str,
    ) -> Sequence[RecordMixin]:
        """
        Load records from the specified table for a sequence of primary key tuples.
        The result is unsorted and skips the records that are not found.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            keys: A sequence of keys in (key_type_or_type_name, *primary_keys) format
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
        """

    @abstractmethod
    def load_where(
        self,
        query: QueryMixin,
        *,
        dataset: str,
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
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """

    @abstractmethod
    def count_where(
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
            restrict_to: Count only the subtypes of this type (defaults to the query target type)
        """

    @abstractmethod
    def save_many_grouped(
        self,
        table: str,
        records: Sequence[RecordProtocol],
        *,
        dataset: str,
    ) -> None:
        """
        Save records grouped by table to the specified table in storage.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            records: Sequence of records
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
        """

    @abstractmethod
    def delete_many_grouped(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
    ) -> None:
        """
        Delete records using an iterable of keys grouped by table.

        Args:
            table: Logical database table name, may be different from the physical name or the key type name
            keys: Sequence of keys
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
            db_type = TypeCache.get_class_from_type_name(db_settings.db_type)

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

    def _get_dataset_table_binding_cache(
        self,
        *,
        dataset: str,
    ) -> dict[tuple[str, str], TableBinding]:
        """Get table binding cache for the specified dataset."""

        if not self._table_binding_cache:
            self._table_binding_cache = {}
        if (result := self._table_binding_cache.get(dataset)) is None:
            query = TableBindingKeyQueryByTable().build()
            bindings = self.load_where(query, cast_to=TableBinding, dataset=dataset)
            result = {(binding.table, binding.record_type): binding for binding in bindings}
            self._table_binding_cache[dataset] = result
        return result

    def _add_binding(
        self,
        *,
        table: str,
        record_type: type[RecordProtocol],
        dataset: str,
    ) -> None:
        """
        Record the table to record type binding in the DB if not found in cache, update cache.

        Args:
            table: Table name in PascalCase format
            record_type: Record type bound to the table
        """

        record_type_name = TypeUtil.name(record_type)
        cache_key = (table, record_type_name)
        if cache_key not in self._get_dataset_table_binding_cache(dataset=dataset):

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
                self._get_dataset_table_binding_cache(dataset=dataset).setdefault(
                    (binding.table, binding.record_type),
                    binding,
                )
                for binding in bindings
            )

            # Save bindings to the dataset
            binding_tables = tuple(set(binding.get_table() for binding in bindings))
            if len(binding_tables) != 1:
                raise RuntimeError("Bindings must be stored in a single table.")
            binding_table = binding_tables[0]
            self.save_many_grouped(binding_table, bindings, dataset=dataset)

    @classmethod
    def _check_dataset(cls, dataset: str) -> None:
        """Error if dataset is None, an empty string, or has invalid format."""
        if dataset is None:
            raise RuntimeError(f"Dataset identifier cannot be None.")
        elif dataset == "":
            raise RuntimeError(f"Dataset identifier cannot be an empty string.")
        elif not isinstance(dataset, str):
            raise RuntimeError(f"Dataset identifier must be a string.")
