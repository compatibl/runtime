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
from typing import Dict, Sequence
from typing import Iterable
from typing_extensions import Self
from cl.runtime import Db
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in cache lookup."""

_local_cache_instance = None
"""Singleton instance is created on first access."""


@dataclass(slots=True, kw_only=True)
class LocalCache(Db):
    """In-memory cache for objects without serialization."""

    __cache: Dict[str, Dict[tuple, RecordProtocol]] = required(default_factory=lambda: {})
    """Record instance is stored in cache without serialization."""

    def load_many_unsorted(
        self,
        record_type: type[TRecord],
        keys: Sequence[tuple],
        *,
        dataset: str | None = None,
    ) -> Sequence[TRecord]:
        # Try to retrieve table dictionary
        key_type = record_type.get_key_type()
        key_type_name = TypeUtil.name(key_type)
        if (table_cache := self.__cache.get(key_type_name, None)) is not None:
            result = []
            for key in keys:
                # Look up the record, defaults to None
                serialized_key = _KEY_SERIALIZER.serialize(key)
                record = table_cache.get(serialized_key, None)
                result.append(record)
            return result
        else:
            # Tables are created on demand, table not found means no records with this key type are stored
            return []

    def load_all(
        self,
        record_type: type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        raise NotImplementedError()

    def load_filter(
        self,
        record_type: type[TRecord],
        filter_obj: TRecord,
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord]:
        raise NotImplementedError()

    def save_many(
        self,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        # TODO: Provide a more performant implementation
        for record in records:
            # Try to retrieve table dictionary using 'key_type' as key, insert if it does not yet exist
            key_type = record.get_key_type()
            key_type_name = TypeUtil.name(key_type)
            table_cache = self.__cache.setdefault(key_type_name, {})

            # Serialize both key and record
            key = record.get_key()
            serialized_key = _KEY_SERIALIZER.serialize(key)

            # Add record to cache, overwriting an existing record if present
            table_cache[serialized_key] = record

    def delete_one(
        self,
        key_type: type[TKey],
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
    ) -> None:
        raise NotImplementedError()

    def delete_many(
        self,
        keys: Iterable[KeyProtocol] | None,
        *,
        dataset: str | None = None,
    ) -> None:
        # Validate the dataset and if necessary convert to delimited string
        raise NotImplementedError()

    def delete_all_and_drop_db(self) -> None:
        """
        IMPORTANT: !!! DESTRUCTIVE - THIS WILL PERMANENTLY DELETE ALL RECORDS WITHOUT THE POSSIBILITY OF RECOVERY

        Notes:
            This method will not run unless both db_id and database start with 'temp_db_prefix'
            specified using Dynaconf and stored in 'DbSettings' class
        """
        # Check that db_id matches temp_db_prefix
        self.error_if_not_temp_db(self.db_id)

        # Create a new cache
        __cache = {}

    def close_connection(self) -> None:
        """Close database connection to releasing resource locks."""
        # Do nothing here, as this is an in-memory cache which does not require a connection

    @classmethod
    def check_db_id(cls, db_id: str) -> None:
        """Check that db_id follows the database name restrictions, error message otherwise."""
        pass  # TODO: Implement validation

    @classmethod
    def instance(cls) -> Self:
        """Return singleton instance."""

        # Check if cached value exists, load if not found
        global _local_cache_instance
        if _local_cache_instance is None:
            # Create if does not yet exist
            _local_cache_instance = LocalCache()
        return _local_cache_instance
