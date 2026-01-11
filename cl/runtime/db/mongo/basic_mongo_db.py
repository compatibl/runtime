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
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.synchronous.collection import Collection
from pymongo.synchronous.cursor import Cursor
from cl.runtime.db.db import Db
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_enum_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typeof
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.db_settings import DbSettings

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

# TODO (Roman): Clean up open connections on worker shutdown
_mongo_client_dict: dict[tuple[type, str | None], MongoClient] = {}
"""Mongo client dict for caching and reusing Mongo connection."""


@dataclass(slots=True, kw_only=True)
class BasicMongoDb(Db):
    """MongoDB database without bitemporal support."""

    client_uri: str | None = None
    """MongoDB client URI, defaults to mongodb://localhost:27017/"""

    _mongo_client: MongoClient | None = None
    """MongoDB client instance, initialized once and stored."""

    _mongo_db_name: str | None = None
    """MongoDB database name, verified and stored."""

    _mongo_db: Database | None = None
    """MongoDB database instance, initialized once and stored."""

    _mongo_collection_dict: dict[type, Collection] | None = None
    """MongoDB collection dict, collections are initialized once and stored."""

    _query_types_with_index: set[type] | None = None
    """Set of query types for which an index has already been added."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        db_settings = DbSettings.instance()

        # Set CouchDB URI from settings if not specified
        if self.client_uri is None:
            # Default to CouchDB URI from settings if not specified in this class
            if db_settings.db_client_uri is not None:
                self.client_uri = db_settings.db_client_uri
            else:
                # If neither is specified, use localhost with the default MongoDB port and no credentials
                self.client_uri = "mongodb://localhost:27017/"

        # Check that variables that are actually used in the URI are set
        client_uri_dict = {}
        if "{db_username}" in self.client_uri:
            NoneChecks.guard_not_none(db_settings.db_username)
            client_uri_dict["db_username"] = db_settings.db_username
        if "{db_password}" in self.client_uri:
            NoneChecks.guard_not_none(db_settings.db_password)
            client_uri_dict["db_password"] = db_settings.db_password

        # Perform variable substitution
        self.client_uri = self.client_uri.format(client_uri_dict)

    def is_empty(self) -> bool:
        """Return true if the database contains no collections."""
        mongo_db = self._get_mongo_db()
        return len(mongo_db.list_collection_names()) == 0

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

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_key_sequence(keys)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Query for all records in one call using $in operator
        serialized_records = collection.find(self._get_mongo_keys_filter(keys, dataset=dataset, tenant=tenant))

        # Apply sort to the iterable
        serialized_records = self._apply_sort(serialized_records, sort_field="_key", sort_order=sort_order)

        # Prune the fields used by Db that are not part of the serialized record data and deserialize
        result = tuple(
            _RECORD_SERIALIZER.deserialize(self._with_pruned_fields(x, expected_dataset=dataset))
            for x in serialized_records
        )
        return cast(tuple[TRecord, ...], result)

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

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Create a query dictionary
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
        }

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # TODO: Filter by keys
        # serialized_primary_key = _KEY_SERIALIZER.serialize(key)
        # serialized_record = collection.find_one({"_key": serialized_primary_key})

        # Get iterable from the query, execution is deferred
        serialized_records = collection.find(query_dict)

        # Apply sort to the iterable
        serialized_records = self._apply_sort(serialized_records, sort_field="_key", sort_order=sort_order)

        # Apply skip and limit to the iterable
        serialized_records = self._apply_limit_and_skip(serialized_records, limit=limit, skip=skip)

        # Prune the fields used by Db that are not part of the serialized record data and deserialize
        result = tuple(
            _RECORD_SERIALIZER.deserialize(self._with_pruned_fields(x, expected_dataset=dataset))
            for x in serialized_records
        )
        return cast(tuple[TRecord, ...], result)

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

        # Check that the query has been frozen
        query.check_frozen()

        # Check dataset
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get table name from key type and check it has an acceptable format
        query_target_type = query.get_target_type()
        key_type = query_target_type.get_key_type()

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(collection=collection, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
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
                f"In {typename(type(self))}.load_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the query target type {typename(query_target_type)} for {typename(type(query))}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Get iterable from the query, execution is deferred
        serialized_records = collection.find(query_dict)

        # Apply sort to the iterable
        serialized_records = self._apply_sort(serialized_records, sort_field="_key", sort_order=sort_order)

        # Apply skip and limit to the iterable
        serialized_records = self._apply_limit_and_skip(serialized_records, limit=limit, skip=skip)

        # Set cast_to to restrict_to if not specified
        if cast_to is None:
            cast_to = restrict_to

        # Prune the fields used by Db that are not part of the serialized record data and deserialize
        result = tuple(
            _RECORD_SERIALIZER.deserialize(self._with_pruned_fields(x, expected_dataset=dataset))
            for x in serialized_records
        )
        return cast(tuple[TRecord, ...], result)

    def count_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> int:

        # Check that the query has been frozen
        query.check_frozen()

        # Check dataset
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get table name from key type and check it has an acceptable format
        query_target_type = query.get_target_type()
        key_type = query_target_type.get_key_type()

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(collection=collection, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
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
                f"In {typename(type(self))}.count_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Use count_documents to get the count
        count = collection.count_documents(query_dict)
        return count

    def save_many(
        self,
        key_type: type[KeyMixin],
        records: Sequence[RecordMixin],
        *,
        dataset: str,
        tenant: str,
        save_policy: SavePolicy,
    ) -> None:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_record_sequence(records)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # TODO: Provide a more performant implementation
        for record in records:
            # Serialize key
            serialized_key = _KEY_SERIALIZER.serialize(record.get_key())
            key_dict = {
                "_dataset": dataset,
                "_key": serialized_key,
                "_tenant": tenant,
            }

            # Serialize record
            serialized_record = _RECORD_SERIALIZER.serialize(record)
            serialized_record["_dataset"] = dataset
            serialized_record["_key"] = serialized_key
            serialized_record["_tenant"] = tenant

            if save_policy == SavePolicy.INSERT:
                collection.insert_one(serialized_record)
            elif save_policy == SavePolicy.REPLACE:
                collection.replace_one(key_dict, serialized_record, upsert=True)
            else:
                ErrorUtil.enum_value_error(save_policy, SavePolicy)

    def delete_many(
        self,
        key_type: type[KeyMixin],
        keys: Sequence[KeyMixin],
        *,
        dataset: str,
        tenant: str,
    ) -> None:

        # Check params
        assert TypeCheck.guard_key_type(key_type)
        assert TypeCheck.guard_key_sequence(keys)
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Create filter and delete
        keys_filter = self._get_mongo_keys_filter(keys, dataset=dataset, tenant=tenant)
        collection.delete_many(keys_filter)

    def delete_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> None:

        # Check that the query has been frozen
        query.check_frozen()

        # Check dataset
        self._check_dataset(dataset)
        self._check_tenant(tenant)

        # Get table name from key type and check it has an acceptable format
        query_target_type = query.get_target_type()
        key_type = query_target_type.get_key_type()

        # Get MongoDB collection for the key type
        collection = self._get_mongo_collection(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(collection=collection, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
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
                f"In {typename(type(self))}.count_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Delete from DB
        collection.delete_many(query_dict)

    def _drop_db_do_not_call_directly(self) -> None:
        """DO NOT CALL DIRECTLY, call drop_db() instead."""
        # Drop the database without possibility of recovery after
        # the preconditions check above to prevent unintended use
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

    def _get_mongo_collection(self, key_type: type[KeyMixin]) -> Collection:
        """Get pymongo collection for the specified key type."""
        if self._mongo_collection_dict is None:
            self._mongo_collection_dict = {}
        if (collection := self._mongo_collection_dict.get(key_type, None)) is None:
            # This also checks that the name of key_type has Key suffix
            assert TypeCheck.guard_key_type(key_type)

            # Get collection object
            mongo_db = self._get_mongo_db()
            key_type_name = typename(key_type)
            collection_name = key_type_name.removesuffix("Key")
            collection = mongo_db[collection_name]

            # Add a unique index on tenant, dataset and key in ascending order
            key_index = (
                ("_tenant", pymongo.ASCENDING),
                ("_dataset", pymongo.ASCENDING),
                ("_key", pymongo.ASCENDING),
            )
            # TODO: !!!! Add updated_index
            collection.create_index(key_index, unique=True, background=True)

            # Cache for reuse
            self._mongo_collection_dict[key_type] = collection
        return collection

    def _get_mongo_client_type(self) -> type:
        """Get the type of MongoDB client object, BasicMongoMockDb overrides this to return the mongomock version."""
        return MongoClient

    def _get_mongo_client(self) -> MongoClient:
        """Get MongoDB client object, MongoMock will override."""

        # TODO (Roman): Refactor. Consider removing _mongo_client from instance-level fields
        if self._mongo_client is None:
            mongo_client_type = self._get_mongo_client_type()

            mongo_client_key = (mongo_client_type, self.client_uri)
            cached_mongo_client = _mongo_client_dict.get(mongo_client_key)

            if cached_mongo_client is None:
                mongo_client = mongo_client_type(
                    self.client_uri,
                    tz_aware=True,
                    uuidRepresentation="standard",
                )
                self._mongo_client = mongo_client
                _mongo_client_dict[mongo_client_key] = mongo_client
            else:
                self._mongo_client = cached_mongo_client

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
        if is_record_type(restrict_to):
            # Add filter condition on type if it is a record type
            child_record_type_names = TypeInfo.get_child_and_self_type_names(restrict_to, type_kind=TypeKind.RECORD)
            query_dict["_type"] = {"$in": child_record_type_names}
        elif is_key_type(restrict_to):
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

    @classmethod
    def _apply_sort(cls, records: Cursor, sort_field: str, sort_order: SortOrder) -> Cursor:
        """Apply sorting to the records using the specified sort field and sort order."""
        if sort_order == SortOrder.UNORDERED:
            return records  # no sort applied
        elif sort_order == SortOrder.ASC:
            return records.sort(sort_field, direction=pymongo.ASCENDING)
        elif sort_order == SortOrder.DESC:
            return records.sort(sort_field, direction=pymongo.DESCENDING)
        elif sort_order == SortOrder.INPUT:
            # Not implemented. Return unchanged records by default.
            return records
        else:
            raise ValueError(f"Unsupported SortOrder: {order}")

    def _with_pruned_fields(
        self,
        record_dict: dict[str, Any],
        *,
        expected_dataset: str,
    ) -> dict[str, Any]:
        """Prune and validate fields that are not part of the serialized record data and return the same instance."""

        # Remove or pop and validate
        del record_dict["_id"]
        assert record_dict.pop("_dataset") == expected_dataset
        del record_dict["_key"]

        return record_dict

    def _get_mongo_keys_filter(self, keys: Sequence[KeyMixin], *, dataset: str, tenant: str) -> dict[str, Any]:
        """Get filter for loading records that match one of the specified keys."""
        serialized_keys = tuple(_KEY_SERIALIZER.serialize(key) for key in keys)
        return {
            "_dataset": dataset,
            "_tenant": tenant,
            "_key": {"$in": serialized_keys},
        }

    def _add_index(
        self,
        *,
        collection: Collection,
        query_type: type,
    ) -> None:
        """Add index for the specified query_type."""
        if not self._query_types_with_index:
            # Create an empty set of query types for which the index has already been added
            self._query_types_with_index = set()
        if query_type not in self._query_types_with_index:

            # First fields in the index
            query_index = [("_tenant", pymongo.ASCENDING), ("_dataset", pymongo.ASCENDING)]
            # Populate query fields recursively
            self._populate_index(type_=query_type, result=query_index)
            # Key is the last field in the index
            query_index.append(("_key", pymongo.ASCENDING))

            # Add index to DB in background mode
            collection.create_index(query_index, unique=True, background=True)
            # Add to the set of query types for which the index has already been added
            self._query_types_with_index.add(query_type)

    def _populate_index(
        self,
        *,
        type_: type,
        field_prefix: str | None = None,
        result: list[tuple[str, int]],
    ) -> None:
        """
        Populate a flat dict of (field_name, ASCENDING | DESCENDING) for the specified type
        with recursion into embedded data, key or record types.
        """
        type_spec = CastUtil.cast(DataSpec, TypeSchema.for_type(type_))
        for field_spec in type_spec.fields:

            # Get type hint and ensure it is not a container
            field_type_hint = field_spec.field_type_hint
            if field_type_hint.remaining:
                raise RuntimeError(
                    f"Field {field_spec.field_name} in type {typename(type_)} is a container and cannot be queried."
                )

            # Combine field prefix with field name
            if field_prefix:
                combined_field_prefix = f"{field_prefix}.{field_spec.field_name}"
            else:
                combined_field_prefix = field_spec.field_name

            # Populate depending on field type
            field_type = field_type_hint.schema_type
            if is_primitive_type(field_type) or is_enum_type(field_type):
                # Add a primitive or enum field
                field_order = pymongo.DESCENDING if field_spec.descending else pymongo.ASCENDING
                result.append((combined_field_prefix, field_order))
            elif is_data_key_or_record_type(field_type):
                # Add a data, key or record field
                self._populate_index(
                    type_=field_type,
                    field_prefix=combined_field_prefix,
                    result=result,
                )
            else:
                raise RuntimeError(f"Cannot create index for field type {typename(field_type)}.")
