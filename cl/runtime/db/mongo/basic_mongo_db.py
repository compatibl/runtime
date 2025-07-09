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

import itertools
import re
from dataclasses import dataclass
from typing import Dict
from typing import Iterable
from typing import Sequence
from memoization import cached
from mongomock import MongoClient as MongoClientMock
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.synchronous.collection import Collection
from cl.runtime import RecordMixin
from cl.runtime.db.db import Db
from cl.runtime.db.mongo.mongo_filter_serializer import MongoFilterSerializer
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.record_util import RecordUtil
from cl.runtime.records.table_util import TableUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
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

    def load_many_unsorted(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> Sequence[RecordMixin]:
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

    def load_all(
        self,
        table: str,
        record_type: type[TKey],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        # Get key type
        if is_record(record_type):
            key_type = record_type.get_key_type()
        elif is_key(record_type):
            key_type = record_type
        else:
            raise RuntimeError(f"Type {TypeUtil.name(record_type)} passed to load_all method is not a record or key.")

        # Get collection name from key type
        db = self._get_mongo_db()
        collection = db[table]

        subtype_names = TypeInfoCache.get_child_names(record_type)
        serialized_records = collection.find({"_type": {"$in": subtype_names}})
        result = []
        for serialized_record in serialized_records:
            del serialized_record["_id"]
            del serialized_record["_key"]
            record = data_serializer.deserialize(serialized_record)  # TODO: Convert to comprehension for performance
            result.append(record)
        return RecordUtil.sort_records_by_key(result)

    def load_where(
        self,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        cast_to: type | None = None,
        # TODO: Add sort
        limit: int | None = None,
        skip: int | None = None,
    ) -> Sequence[RecordMixin]:
        # Check that query has been frozen
        query.check_frozen()

        # Get record type from the query and key type from the record
        record_type = query.get_record_type()
        if cast_to is None:
            # Limit returned results to record_type if cast_to is not specified
            cast_to = record_type
        else:
            # Ensure cast_to is a subclass of query_record_type
            if not issubclass(cast_to, record_type):
                raise RuntimeError(
                    f"In {TypeUtil.name(self)}.load_where, cast_to={TypeUtil.name(cast_to)} which is not a subclass\n"
                    f"of the type {TypeUtil.name(record_type)} returned by {TypeUtil.name(query)}.get_record_type()."
                )

        # Get collection using table name from the query
        table = query.get_table()
        collection = self._get_mongo_collection(table)

        # Serialize the query
        query_dict = DataSerializers.FOR_MONGO.serialize(query)
        # TODO: Remove table fields

        # Add condition on type
        subtype_names = TypeInfoCache.get_child_names(cast_to)
        query_dict["_type"] = {"$in": subtype_names}

        serialized_records = collection.find(query_dict)
        result = []
        for serialized_record in serialized_records:
            del serialized_record["_id"]
            del serialized_record["_key"]
            record = data_serializer.deserialize(serialized_record)  # TODO: Convert to comprehension for performance
            result.append(record)
        return RecordUtil.sort_records_by_key(result)  # TODO: Decide on the default sorting method

    def save_many(
        self,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:
        # TODO: Provide a more performant implementation

        # Add Table objects to save at the end
        # TODO (Roman): Improve performance
        tables = TableUtil.get_tables_in_records(records)
        records_to_save = itertools.chain(records, tables)

        for record in records_to_save:
            table = TableUtil.get_table(record)

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

    def delete_one(
        self,
        key_type: type[TKey],
        key: TKey | KeyProtocol | tuple | str | None,
        *,
        dataset: str | None = None,
    ) -> None:
        # Get collection name from key type by removing Key suffix if present
        collection_name = TypeUtil.name(key_type)  # TODO: Decision on short alias
        db = self._get_mongo_db()
        collection = db[collection_name]

        serialized_key = _KEY_SERIALIZER.serialize(key)

        delete_filter = {"_key": serialized_key}
        collection.delete_one(delete_filter)

    def delete_many(
        self,
        keys: Iterable[KeyProtocol] | None,
        *,
        dataset: str | None = None,
    ) -> None:
        for key in keys:
            self.delete_one(type(key), key, dataset=dataset)

    def drop_temp_db(self) -> None:
        # Check that db_id and db_name both match temp_db_prefix
        db_name = self._get_db_name()

        # Error if db_id does not start from the db_temp_prefix specified in settings.yaml (defaults to 'temp_')
        self.error_if_not_temp_db()

        # Drop the entire database without possibility of recovery, this
        # relies on the temp_db_prefix check above to prevent unintended use
        client = self._get_mongo_client()
        client.drop_database(db_name)

    def close_connection(self) -> None:
        if (client := _client_dict.get(self.client_uri, None)) is not None:
            # Close connection
            client.close()
            # Remove client from dictionary so connection can be reopened on next access
            del _client_dict[self.client_uri]

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

    # TODO (Roman): move to base Db class or remove?
    def is_empty(self) -> bool:
        """Return True if db has no collections."""
        return len(self._get_mongo_db().list_collection_names()) == 0
