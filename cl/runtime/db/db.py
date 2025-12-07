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
from typing import Sequence, final
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.typename import typenameof
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.server.env import Env
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.env_settings import EnvSettings


@dataclass(slots=True, kw_only=True)
class Db(DbKey, RecordMixin, ABC):
    """Polymorphic data storage with dataset isolation."""

    def get_key(self) -> DbKey:
        return DbKey(db_id=self.db_id).build()

    @abstractmethod
    def is_empty(self) -> bool:
        """Return true if the database contains no collections."""

    @abstractmethod
    def load_many(
        self,
        key_type: type[KeyMixin],
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
        tenant: str,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder,  # Default value not provided due to the lack of natural default for this method
    ) -> tuple[RecordMixin, ...]:
        """
        Load records for the specified keys, skipping the records that are not found.

        Args:
            key_type: Key type determines the database table
            keys: Sequence of keys, type(key) must match the key_type argument for each key
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """

    @abstractmethod
    def load_all(
        self,
        key_type: type[KeyMixin],
        *,
        dataset: str,
        tenant: str,
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
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: Include only this type and its subtypes, skip other types
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
        tenant: str,
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
            query: Contains predicates to match
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: Include only this type and its subtypes, skip other types
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
        tenant: str,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query.

        Args:
            query: Contains predicates to match
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            restrict_to: Include only this type and its subtypes, skip other types
        """

    @abstractmethod
    def save_many(
        self,
        key_type: type[KeyMixin],
        records: Sequence[RecordMixin],
        *,
        dataset: str,
        tenant: str,
        save_policy: SavePolicy,
    ) -> None:
        """
        Save multiple records, all of which must have the specified key type.

        Args:
            key_type: Key type determines the database table
            records: Sequence of records to save, record.get_key_type() must match the key_type argument for each record
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            save_policy: Insert vs. replace policy, partial update is not included due to design considerations
        """

    @abstractmethod
    def delete_many(
        self,
        key_type: type[KeyMixin],
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
        tenant: str,
    ) -> None:
        """
        Delete multiple records, all of which must have the specified key type.

        Args:
            key_type: Key type determines the database table
            keys: Sequence of keys to delete, type(key) must match the key_type argument for each key
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
        """

    @abstractmethod
    def delete_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> None:
        """
        Delete records that match the specified query.

        Args:
            query: Contains predicates to match
            dataset: Backslash-delimited dataset argument is combined with self.base_dataset if specified
            tenant: Unique tenant identifier, tenants are isolated when sharing the same DB
            restrict_to: Include only this type and its subtypes, skip other types
        """
        
    @abstractmethod
    def close_connection(self) -> None:  # TODO: !!! Check if this should be done using a context manager instead
        """Close database connection to releasing resource locks."""

    @abstractmethod
    def _drop_db_do_not_call_directly(self) -> None:
        """DO NOT CALL DIRECTLY because this method does not check user approval, call drop_db() instead."""

    @final
    def drop_db(self, *, interactive: bool = False) -> None:
        """
        Drop DB after checking preconditions, request user approval if required and interactive is true.

        Notes:
            This method is marked as final to prevent overrides that bypass the preconditions check.
            The actual drop is performed by the implementation of the _drop_db_do_not_call_directly() method.
        """

        # Ensure interactive is boolean rather than any other truthy or falsy value
        if not isinstance(interactive, bool):
            type_name = typenameof(interactive)
            raise RuntimeError(f"Parameter interactive must a bool value, type {type_name} found.")

        env_kind = EnvSettings.instance().env_kind
        if env_kind in (EnvKind.TEMP, EnvKind.TEST):
            # Dropping DB is allowed without requesting approval for TEMP and TEST, proceed to drop DB
            # TODO: !!! Implement MCP rule to check _drop_db_do_not_call_directly() is only called inside this method
            self._drop_db_do_not_call_directly()
        elif env_kind in (EnvKind.UAT, EnvKind.DEV):
            # Dropping DB is allowed with approval for UAT and DEV
            if interactive:
                # Request user approval in interactive mode
                try:
                    print(f"DATABASE {self.db_id} WILL BE DELETED. THIS ACTION CANNOT BE UNDONE (yes/no): ")
                    user_response = input().strip().lower()
                    if user_response == "yes":
                        print(f"User permission to drop DB {self.db_id} is granted.")
                        # Permission granted, proceed to drop DB
                        self._drop_db_do_not_call_directly()
                    else:
                        raise RuntimeError(f"User permission to drop DB {self.db_id} is denied.")
                except (EOFError, KeyboardInterrupt):
                    raise RuntimeError("\nDB drop operation aborted by the user.\n")
            else:
                raise RuntimeError(
                    f"Dropping DB requires interactive user approval for env_kind={env_kind.name}.\n"
                    f"Contact your DB admin for assistance or execute this command in interactive mode.\n"
                )
        elif env_kind == EnvKind.PROD:
            raise RuntimeError(
                f"Dropping DB from code is not allowed even with user approval for env_kind={env_kind.name}.\n"
                f"Contact your DB admin for assistance.")
        else:
            raise ErrorUtil.enum_value_error(env_kind, EnvKind)

    @classmethod
    def create(cls, *, db_type: type | None = None, db_id: str | None = None):  # TODO: !!!!! Replace by the standard way to create from settings
        """Create DB of the specified type, or use DB type from context settings if not specified."""

        # Get DB settings instance for the lookup of defaults
        db_settings = DbSettings.instance()

        # Get DB type from context settings if not specified
        if db_type is None:
            db_type = TypeInfo.from_type_name(db_settings.db_type)

        # Get DB identifier if not specified
        if db_id is None:
            if not active_or_default(Env).is_test():
                db_id = db_settings.db_id
            else:
                raise RuntimeError("Use pytest fixtures to create temporary DBs inside tests.")

        # Create and return a new DB instance
        return db_type(db_id=db_id).build()

    @classmethod
    def _check_dataset(cls, dataset: str) -> None:
        """Error if dataset is None, an empty string, or has invalid format."""
        if dataset is None:
            raise RuntimeError(f"Dataset identifier cannot be None.")
        elif dataset == "":
            raise RuntimeError(f"Dataset identifier cannot be an empty string.")
        elif not isinstance(dataset, str):
            raise RuntimeError(f"Dataset identifier must be a string.")

    @classmethod
    def _check_tenant(cls, tenant: str) -> None:
        """Error if tenant is None, an empty string, or has invalid format."""
        if tenant is None:
            raise RuntimeError(f"Tenant identifier cannot be None.")
        elif tenant == "":
            raise RuntimeError(f"Tenant identifier cannot be an empty string.")
        elif not isinstance(tenant, str):
            raise RuntimeError(f"Tenant identifier must be a string.")
