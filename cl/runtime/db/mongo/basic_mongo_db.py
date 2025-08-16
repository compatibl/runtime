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

import re
from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Sequence
from typing import cast
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.synchronous.collection import Collection
from cl.runtime import RecordMixin
from cl.runtime.db.db import Db
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_INVALID_DB_NAME_SYMBOLS = r'/\\. "$*<>:|?'
"""Invalid MongoDB database name symbols."""

_INVALID_DB_NAME_SYMBOLS_MSG = r'<space>/\."$*<>:|?'
"""Invalid MongoDB database name symbols (for the error message)."""

_INVALID_DB_NAME_REGEX = re.compile(f"[{_INVALID_DB_NAME_SYMBOLS}]")
"""Precompiled regex to check for invalid MongoDB database name symbols."""

_RECORD_SERIALIZER = DataSerializers.FOR_MONGO
"""Used for record serialization."""

_KEY_SERIALIZER = KeySerializers.DELIMITED
"""Used for key serialization."""


@dataclass(slots=True, kw_only=True)
class BasicMongoDb(Db):
    """MongoDB database without bitemporal support."""

    client_uri: str = "mongodb://localhost:27017/"
    """MongoDB client URI, defaults to mongodb://localhost:27017/"""

    _mongo_client: MongoClient | None = None
    """MongoDB client instance, initialized once and stored."""

    _mongo_db_name: str | None = None
    """MongoDB database name, verified and stored."""

    _mongo_db: Database | None = None
    """MongoDB database instance, initialized once and stored."""

    _mongo_collection_dict: dict[type, Collection] | None = None
    """MongoDB collection dict, collections are initialized once and stored."""

    def load_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
        sort_order: SortOrder = SortOrder.INPUT,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> Sequence[RecordMixin]:

        # Check params
        assert TypeCheck.is_key_type(key_type)
        assert TypeCheck.is_key_sequence(keys)
        self._check_dataset(dataset)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)
        result = []
        for key in keys:
            # TODO: Implement using a more performant approach
            serialized_primary_key = _KEY_SERIALIZER.serialize(key)
            serialized_record = collection.find_one({"_key": serialized_primary_key})

            # Do not include None if the record is not found, skip instead
            if serialized_record is not None:
                del serialized_record["_id"]
                del serialized_record["_key"]
                record = _RECORD_SERIALIZER.deserialize(serialized_record)
                result.append(record)
        return result

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

        # Check params
        assert TypeCheck.is_key_type(key_type)
        self._check_dataset(dataset)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Create a query dictionary
        query_dict = {}

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # TODO: Filter by keys
        # serialized_primary_key = _KEY_SERIALIZER.serialize(key)
        # serialized_record = collection.find_one({"_key": serialized_primary_key})

        # Get iterable from the query sorted by '_key', execution is deferred
        serialized_records = collection.find(query_dict).sort("_key")

        # Apply skip and limit to the iterable
        serialized_records = self._apply_limit_and_skip(serialized_records, limit=limit, skip=skip)

        result = tuple(
            _RECORD_SERIALIZER.deserialize({k: v for k, v in serialized_record.items() if k not in {"_id", "_key"}})
            for serialized_record in serialized_records
        )
        return cast(tuple[TRecord, ...], result)

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

        # Check that query has been frozen
        query.check_frozen()

        # Check dataset
        self._check_dataset(dataset)

        # Get table name from key type and check it has an acceptable format
        query_target_type = query.get_target_type()
        key_type = query_target_type.get_key_type()

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Serialize the query
        query_dict = BootstrapSerializers.FOR_MONGO_QUERY.serialize(query)
        # TODO: Remove table fields

        # Convert op_* fields to MongoDB $* syntax
        query_dict = self._convert_op_fields_to_mongo_syntax(query_dict)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query_target_type
        elif not issubclass(restrict_to, query_target_type):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {typename(self)}.load_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the query target type {typename(query_target_type)} for {typename(query)}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Get iterable from the query sorted by '_key', execution is deferred
        serialized_records = collection.find(query_dict).sort("_key")

        # Apply skip and limit to the iterable
        serialized_records = self._apply_limit_and_skip(serialized_records, limit=limit, skip=skip)

        # Set cast_to to restrict_to if not specified
        if cast_to is None:
            cast_to = restrict_to

        result: list[TRecord] = []
        # TODO: Convert to comprehension for performance
        for serialized_record in serialized_records:
            del serialized_record["_id"]
            del serialized_record["_key"]

            # Create a record from the serialized data
            record = _RECORD_SERIALIZER.deserialize(serialized_record)

            # Apply cast (error if not a subtype)
            record = record.cast(cast_to)
            result.append(record)

        return tuple(result)

    def count_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        restrict_to: type | None = None,
    ) -> int:

        # Check that query has been frozen
        query.check_frozen()

        # Check dataset
        self._check_dataset(dataset)

        # Get table name from key type and check it has an acceptable format
        query_target_type = query.get_target_type()
        key_type = query_target_type.get_key_type()

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Serialize the query
        query_dict = BootstrapSerializers.FOR_MONGO_QUERY.serialize(query)
        # TODO: Remove table fields

        # Convert op_* fields to MongoDB $* syntax
        query_dict = self._convert_op_fields_to_mongo_syntax(query_dict)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query_target_type
        elif not issubclass(restrict_to, query_target_type):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {typename(self)}.load_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Use count_documents to get the count
        count = collection.count_documents(query_dict)
        return count

    def save_many(
        self,
        key_type: type[KeyProtocol],
        records: Sequence[RecordProtocol],
        *,
        dataset: str,
    ) -> None:

        # Check params
        assert TypeCheck.is_key_type(key_type)
        assert TypeCheck.is_record_sequence(records)
        self._check_dataset(dataset)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # TODO: Provide a more performant implementation
        for record in records:

            # Add to the cache of stored types for the specified dataset
            self._add_record_type(record_type=type(record), dataset=dataset)

            # Serialize data, this also executes 'init_all' method
            serialized_record = _RECORD_SERIALIZER.serialize(record)

            # Serialize key
            # TODO: Consider getting the key first instead of serializing the entire record
            serialized_key = _KEY_SERIALIZER.serialize(record.get_key())

            # Use update_one with upsert=True to insert if not present or update if present
            # TODO (Roman): update_one does not affect fields not presented in record. Changed to replace_one
            serialized_record["_key"] = serialized_key
            collection.replace_one({"_key": serialized_key}, serialized_record, upsert=True)

    def delete_many(
        self,
        key_type: type[KeyProtocol],
        keys: Sequence[KeyProtocol],
        *,
        dataset: str,
    ) -> None:

        # Check params
        assert TypeCheck.is_key_type(key_type)
        assert TypeCheck.is_key_sequence(keys)
        self._check_dataset(dataset)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)
        for key in keys:
            # TODO: Implement using a more performant approach
            serialized_primary_key = _KEY_SERIALIZER.serialize(key)
            collection.delete_one({"_key": serialized_primary_key})

    def drop_test_db(self) -> None:
        # Check preconditions
        self.check_drop_test_db_preconditions()

        # Drop the entire database without possibility of recovery.
        # This relies on the preconditions check above to prevent unintended use
        client = self._get_mongo_client()
        db_name = self._get_db_name()
        client.drop_database(db_name)

    def drop_temp_db(self, *, user_approval: bool) -> None:
        # Check preconditions
        self.check_drop_temp_db_preconditions(user_approval=user_approval)

        # Drop the entire database without possibility of recovery.
        # This relies on the preconditions check above to prevent unintended use
        client = self._get_mongo_client()
        db_name = self._get_db_name()
        client.drop_database(db_name)

    def close_connection(self) -> None:
        # TODO: Review the use of this method and when it is invoked
        self._get_mongo_client().close()

    def _convert_op_fields_to_mongo_syntax(self, query_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert op_* fields to MongoDB $* syntax recursively."""
        if not isinstance(query_dict, dict):
            return query_dict

        result = {}
        for key, value in query_dict.items():
            if key.startswith("op_"):
                # Convert op_* to $* syntax
                mongo_key = "$" + key[3:]  # Remove "op_" prefix
                result[mongo_key] = value
            elif isinstance(value, dict):
                # Recursively convert nested dictionaries
                result[key] = self._convert_op_fields_to_mongo_syntax(value)
            elif isinstance(value, list):
                # Recursively convert list items
                result[key] = [
                    self._convert_op_fields_to_mongo_syntax(item) if isinstance(item, dict) else item for item in value
                ]
            else:
                # Keep other values as-is
                result[key] = value

        return result

    def _get_mongo_collection(self, key_type: type[KeyProtocol]) -> Collection:
        """Get pymongo collection for the specified key type."""
        if self._mongo_collection_dict is None:
            self._mongo_collection_dict = {}
        if (collection := self._mongo_collection_dict.get(key_type, None)) is None:
            # This also checks that the name of key_type has Key suffix
            assert TypeCheck.is_key_type(key_type)

            # Get collection object
            mongo_db = self._get_mongo_db()
            key_type_name = typename(key_type)
            collection_name = key_type_name.removesuffix("Key")
            collection = mongo_db[collection_name]

            # Add an index on tenant, dataset and key in ascending order
            collection.create_index(
                [
                    # ("_tenant", 1),
                    # ("_dataset", 1),
                    ("_key", 1),
                ],
            )

            # Cache for reuse
            self._mongo_collection_dict[key_type] = collection
        return collection

    def _get_mongo_client_type(self) -> type:
        """Get the type of MongoDB client object, BasicMongoMockDb overrides this to return the mongomock version."""
        return MongoClient

    def _get_mongo_client(self) -> MongoClient:
        """Get MongoDB client object, MongoMock will override."""
        if self._mongo_client is None:
            mongo_client_type = self._get_mongo_client_type()
            self._mongo_client = mongo_client_type(
                self.client_uri,
                tz_aware=True,
                uuidRepresentation="standard",
            )
        return self._mongo_client

    def _get_db_name(self) -> str:
        """For MongoDB, database name is db_id, perform validation before returning."""
        if self._mongo_db_name is None:
            self._mongo_db_name = self.db_id
            # Check for invalid characters in MongoDB name
            if _INVALID_DB_NAME_REGEX.search(self._mongo_db_name):
                raise RuntimeError(
                    f"MongoDB database name '{self._mongo_db_name}' is not valid because it contains "
                    f"special characters from this list: '{_INVALID_DB_NAME_SYMBOLS_MSG}'"
                )

            # Check for maximum byte length of less than 64 (use Unicode bytes, not string chars to count)
            max_bytes = 63
            actual_bytes = len(self._mongo_db_name.encode("utf-8"))
            if actual_bytes > max_bytes:
                raise RuntimeError(
                    f"MongoDB does not support database name '{self._mongo_db_name}' because "
                    f"it has {actual_bytes} bytes, exceeding the maximum of {max_bytes}."
                )
        return self._mongo_db_name

    def _get_mongo_db(self) -> Database:
        """Get or create the pymongo database object."""
        if self._mongo_db is None:
            db_name = self._get_db_name()
            client = self._get_mongo_client()
            self._mongo_db = client[db_name]
        return self._mongo_db

    @classmethod
    def _apply_restrict_to(
        cls,
        *,
        query_dict: dict,
        key_type: type,
        restrict_to: type | None,
    ) -> None:
        """Add filter by the specified type to the query dictionary."""
        if restrict_to is None:
            # Do nothing if restrict_to is not specified
            return
        if is_record(restrict_to):
            # Add filter condition on type if it is a record type
            child_record_type_names = TypeCache.get_child_type_names(restrict_to, type_kind=TypeKind.RECORD)
            query_dict["_type"] = {"$in": child_record_type_names}
        elif is_key(restrict_to):
            # Check that it matches the key type obtained from the query
            if restrict_to != key_type:
                raise RuntimeError(
                    f"Parameter restrict_to={typename(restrict_to)} does not match " f"key_type={typename(key_type)}."
                )
        else:
            raise RuntimeError(f"Parameter restrict_to={typename(restrict_to)} is not a key or record.")

    @classmethod
    def _apply_limit_and_skip(
        cls,
        serialized_records: Iterable,
        *,
        limit: int | None = None,
        skip: int | None = None,
    ) -> Iterable:
        """Apply limit and skip to the records iterable."""
        # Apply skip
        if skip is not None:
            if skip > 0:
                # Apply skip to iterable
                serialized_records = serialized_records.skip(skip)
            elif skip == 0:
                # We interpret skip=0 as not skipping, do nothing
                pass
            else:
                raise RuntimeError(f"Parameter skip={skip} is negative.")

        # Apply limit
        if limit is not None:
            if limit > 0:
                # Apply limit to iterable
                serialized_records = serialized_records.limit(limit)
            elif limit == 0:
                # Handle this case separately because pymongo interprets limit=0 as no limit,
                # while we interpret it as returning no records
                return tuple()
            else:
                raise RuntimeError(f"Parameter limit={limit} is negative.")
        return serialized_records
