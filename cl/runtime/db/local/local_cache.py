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
from typing import Sequence
from cl.runtime.db.db import Db
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in cache lookup."""

_local_cache_instance = None
"""Singleton instance is created on first access."""


@dataclass(slots=True, kw_only=True)
class LocalCache(Db):
    """In-memory cache for objects without serialization."""

    __cache: dict[type[KeyProtocol], dict[tuple, RecordProtocol]] = required(default_factory=lambda: {})
    """Record instance is stored in cache without serialization."""

    def load_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder,  # Default value not provided due to the lack of natural default for this method
    ) -> Sequence[RecordMixin]:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_key_sequence(keys)
        self._check_dataset(dataset)

        if (table_cache := self.__cache.get(key_type, None)) is not None:
            result = []
            for key in keys:
                # Look up the record, defaults to None
                serialized_key = _KEY_SERIALIZER.serialize(key)  # Use hash instead?
                record = table_cache.get(serialized_key, None)
                result.append(record)
            return result
        else:
            # Tables are created on demand, table not found means no records with this key type are stored
            return []

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
        raise NotImplementedError()

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
        raise NotImplementedError()

    def count_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        restrict_to: type | None = None,
    ) -> int:
        raise NotImplementedError()

    def save_many(
        self,
        key_type: type[KeyProtocol],
        records: Sequence[RecordProtocol],
        *,
        dataset: str,
        save_policy: SavePolicy,
    ) -> None:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_record_sequence(records)
        self._check_dataset(dataset)

        # TODO: Provide a more performant implementation
        for record in records:
            # Try to retrieve table dictionary, insert if it does not yet exist
            table_cache = self.__cache.setdefault(key_type, {})

            # Serialize both key and record
            key = record.get_key()
            serialized_key = _KEY_SERIALIZER.serialize(key)

            if save_policy == SavePolicy.INSERT:
                # Insert the record, error if already exists
                if serialized_key in table_cache:
                    raise RuntimeError(f"Key {serialized_key} already exists in cache while INSERT policy is selected.")
                table_cache[serialized_key] = record
            elif save_policy == SavePolicy.REPLACE:
                # Add record to cache, overwriting an existing record if present
                table_cache[serialized_key] = record
            else:
                ErrorUtil.enum_value_error(save_policy, SavePolicy)

    def delete_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
    ) -> None:
        raise NotImplementedError()

    def drop_test_db(self) -> None:
        # Check preconditions
        self.check_drop_test_db_preconditions()

        # Create a new cache, the objects in the old cache will no longer be accessible.
        # This relies on the preconditions check above to prevent unintended use
        __cache = {}

    def drop_temp_db(self, *, user_approval: bool) -> None:
        # Check preconditions
        self.check_drop_temp_db_preconditions(user_approval=user_approval)

        # Create a new cache, the objects in the old cache will no longer be accessible.
        # This relies on the preconditions check above to prevent unintended use
        __cache = {}

    def close_connection(self) -> None:
        """Close database connection to releasing resource locks."""
        # TODO: Review if this should be in __exit__ method
        # Do nothing here, as this is an in-memory cache which does not require a connection
