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
from typing import Dict
from typing import Iterable
from typing import Sequence
from typing import cast
from memoization import cached
from mongomock import MongoClient as MongoClientMock
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.synchronous.collection import Collection
from cl.runtime import RecordMixin
from cl.runtime.db.db import Db
from cl.runtime.db.mongo.mongo_filter_serializer import MongoFilterSerializer
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

invalid_db_name_symbols = r'/\\. "$*<>:|?'
"""Invalid MongoDB database name symbols."""

invalid_db_name_symbols_msg = r'<space>/\."$*<>:|?'
"""Invalid MongoDB database name symbols (for the error message)."""

invalid_db_name_regex = re.compile(f"[{invalid_db_name_symbols}]")
"""Precompiled regex to check for invalid MongoDB database name symbols."""

# TODO: Revise and consider making fields of the database
# TODO: Review and consider alternative names, e.g. DataSerializer or RecordSerializer
data_serializer = DataSerializers.FOR_MONGO
"""Default bidirectional dict serializer settings for MongoDB."""

_KEY_SERIALIZER = KeySerializers.DELIMITED
filter_serializer = MongoFilterSerializer()

_client_dict: Dict[str, MongoClient] = {}
"""Dict of MongoClient instances with client_uri key stored outside the class to avoid serializing them."""

_db_dict: Dict[str, Database] = {}
"""Dict of database instances with client_uri.database_name key stored outside the class to avoid serializing them."""


@dataclass(slots=True, kw_only=True)
class BasicMongoDb(Db):
    """MongoDB database without datasets."""

    client_uri: str = "mongodb://localhost:27017/"
    """MongoDB client URI, defaults to mongodb://localhost:27017/"""

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

        # Check dataset
        self._check_dataset(dataset)

        # Get collection
        collection = self._get_mongo_collection(table)

        # Filter by type
        query_dict = {}
        if restrict_to is not None:
            # Add filter condition on type
            subtype_names = TypeCache.get_child_names(restrict_to)
            query_dict["_type"] = {"$in": subtype_names}

        # TODO: Filter by keys
        # serialized_primary_key = _KEY_SERIALIZER.serialize(key)
        # serialized_record = collection.find_one({"_key": serialized_primary_key})

        # Get iterable from the query sorted by '_key', execution is deferred
        serialized_records = collection.find(query_dict).sort("_key")

        # Apply skip and limit to the iterable
        serialized_records = self._apply_limit_and_skip(serialized_records, limit=limit, skip=skip)

        result = tuple(
            data_serializer.deserialize({k: v for k, v in serialized_record.items() if k not in {"_id", "_key"}})
            for serialized_record in serialized_records
        )
        return cast(tuple[TRecord, ...], result)

    def load_many_unsorted(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
    ) -> Sequence[RecordMixin]:

        # Check dataset
        self._check_dataset(dataset)

        # Get Mongo collection using table name
        collection = self._get_mongo_collection(table)
        result = []
        for key in keys:
            # TODO: Implement using a more performant approach
            serialized_primary_key = _KEY_SERIALIZER.serialize(key)
            serialized_record = collection.find_one({"_key": serialized_primary_key})

            # Do not include None if the record is not found, skip instead
            if serialized_record is not None:
                del serialized_record["_id"]
                del serialized_record["_key"]
                record = data_serializer.deserialize(serialized_record)
                result.append(record)
        return result

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

        # Check dataset
        self._check_dataset(dataset)

        # Check that query has been frozen
        query.check_frozen()

        # Get collection using table name from the query
        table = query.get_table()
        collection = self._get_mongo_collection(table)

        # Serialize the query
        query_dict = BootstrapSerializers.FOR_MONGO_QUERY.serialize(query)
        # TODO: Remove table fields

        # Convert op_* fields to MongoDB $* syntax
        query_dict = self._convert_op_fields_to_mongo_syntax(query_dict)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query.get_target_type()
        elif not issubclass(restrict_to, (query_target_type := query.get_target_type())):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {TypeUtil.name(self)}.load_where, restrict_to={TypeUtil.name(restrict_to)} is not a subclass\n"
                f"of the target type {TypeUtil.name(query_target_type)} for {TypeUtil.name(query)}."
            )

        # Add filter condition on type
        subtype_names = TypeCache.get_child_names(restrict_to)
        query_dict["_type"] = {"$in": subtype_names}

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
            record = data_serializer.deserialize(serialized_record)

            # Apply cast (error if not a subtype)
            record = record.cast(cast_to)
            result.append(record)

        return tuple(result)

    def count_where(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        restrict_to: type | None = None,
    ) -> int:

        # Check dataset
        self._check_dataset(dataset)

        """Return the count of documents matching the query using MongoDB's count_documents."""
        # Check that query has been frozen
        query.check_frozen()

        # Get collection using table name from the query
        table = query.get_table()
        collection = self._get_mongo_collection(table)

        # Serialize the query
        query_dict = BootstrapSerializers.FOR_MONGO_QUERY.serialize(query)
        # TODO: Remove table fields

        # Convert op_* fields to MongoDB $* syntax
        query_dict = self._convert_op_fields_to_mongo_syntax(query_dict)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query.get_target_type()
        elif not issubclass(restrict_to, (query_target_type := query.get_target_type())):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {TypeUtil.name(self)}.load_where, restrict_to={TypeUtil.name(restrict_to)} is not a subclass\n"
                f"of the target type {TypeUtil.name(query_target_type)} for {TypeUtil.name(query)}."
            )

        # Add filter condition on type
        subtype_names = TypeCache.get_child_names(restrict_to)
        query_dict["_type"] = {"$in": subtype_names}

        # Use count_documents to get the count
        count = collection.count_documents(query_dict)
        return count

    def save_many_grouped(
        self,
        table: str,
        records: Sequence[RecordProtocol],
        *,
        dataset: str,
    ) -> None:

        # Check dataset
        self._check_dataset(dataset)

        # TODO: Provide a more performant implementation
        for record in records:
            table = record.get_table()

            # Add table binding
            self._add_binding(table=table, record_type=type(record), dataset=dataset)

            db = self._get_mongo_db()
            collection = db[table]

            # Serialize data, this also executes 'init_all' method
            serialized_record = data_serializer.serialize(record)

            # Serialize key
            # TODO: Consider getting the key first instead of serializing the entire record
            serialized_key = _KEY_SERIALIZER.serialize(record.get_key())

            # Use update_one with upsert=True to insert if not present or update if present
            # TODO (Roman): update_one does not affect fields not presented in record. Changed to replace_one
            serialized_record["_key"] = serialized_key
            collection.replace_one({"_key": serialized_key}, serialized_record, upsert=True)

    def delete_many_grouped(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
    ) -> None:

        # Check dataset
        self._check_dataset(dataset)

        # Get Mongo collection using table name
        collection = self._get_mongo_collection(table)
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
        if (client := _client_dict.get(self.client_uri, None)) is not None:
            # Close connection
            client.close()
            # Remove client from dictionary so connection can be reopened on next access
            del _client_dict[self.client_uri]

    def _convert_op_fields_to_mongo_syntax(self, query_dict: Dict[str, Any]) -> Dict[str, Any]:
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

    def _get_mongo_collection(self, table: str) -> Collection:
        """Get PyMongo collection for the specified table."""
        mongo_db = self._get_mongo_db()
        # TODO: Perform table name validation and correction here
        collection_name = table
        result = mongo_db[collection_name]
        return result

    def _get_mongo_db(self) -> Database:
        """Get PyMongo database object."""
        db_name = self._get_db_name()
        db_key = f"{self.client_uri}{db_name}"
        if (result := _db_dict.get(db_key, None)) is None:
            # Create if it does not exist
            client = self._get_mongo_client()
            # TODO: Implement dispose logic
            result = client[db_name]
            _db_dict[db_key] = result
        return result

    def _get_mongo_client(self) -> MongoClient:
        """Get PyMongo client object."""
        if (client := _client_dict.get(self.client_uri, None)) is None:
            # Determine regular or mock client type based on the presence of 'Mock' substring in class name
            if "Mock" in TypeUtil.name(self):
                client_type = MongoClientMock
            else:
                client_type = MongoClient
            # Create client
            client = client_type(
                self.client_uri,
                tz_aware=True,
                uuidRepresentation="standard",
            )
            # TODO: Implement dispose logic
            _client_dict[self.client_uri] = client
        return client

    @cached
    def _get_db_name(self) -> str:
        """For MongoDB, database name is db_id, perform validation before returning."""

        # Check for invalid characters in MongoDB name
        if invalid_db_name_regex.search(self.db_id):
            raise RuntimeError(
                f"MongoDB db_id='{self.db_id}' is not valid because it contains "
                f"special characters from this list: '{invalid_db_name_symbols_msg}'"
            )

        # Check for maximum byte length of less than 64 (use Unicode bytes, not string chars to count)
        max_bytes = 63
        actual_bytes = len(self.db_id.encode("utf-8"))
        if actual_bytes > max_bytes:
            raise RuntimeError(
                f"MongoDB does not support db_id='{self.db_id}' because "
                f"it has {actual_bytes} bytes, exceeding the maximum of {max_bytes}."
            )

        return self.db_id

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

    # TODO (Roman): move to base Db class or remove?
    def is_empty(self) -> bool:
        """Return True if db has no collections."""
        return len(self._get_mongo_db().list_collection_names()) == 0
