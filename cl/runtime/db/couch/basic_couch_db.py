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
from pycouchdb import Server
from pycouchdb.exceptions import NotFound
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

_INVALID_DB_NAME_SYMBOLS = r'/\\. "$*<>:|?' # TODO: !!! Update for CouchDB
"""Invalid CouchDB database name symbols."""

_INVALID_DB_NAME_SYMBOLS_MSG = r'<space>/\."$*<>:|?'  # TODO: !!! Update for CouchDB
"""Invalid CouchDB database name symbols (for the error message)."""

_INVALID_DB_NAME_REGEX = re.compile(f"[{_INVALID_DB_NAME_SYMBOLS}]")
"""Precompiled regex to check for invalid CouchDB database name symbols."""

_RECORD_SERIALIZER = DataSerializers.FOR_MONGO
"""Used for record serialization."""

_KEY_SERIALIZER = KeySerializers.DELIMITED
"""Used for key serialization."""

# TODO (Roman): Clean up open connections on worker shutdown
_couch_server_dict: dict[str, Server] = {}
"""CouchDB server dict for caching and reusing CouchDB connection."""


@dataclass(slots=True, kw_only=True)
class BasicCouchDb(Db):
    """CouchDB database without bitemporal support."""

    client_uri: str | None = None
    """
    Client URI is taken from DbSettings when not specified, must include credentials.
    Example: http://username:password@localhost:5984/
    """

    _couch_server: Server | None = None
    """CouchDB server instance, initialized once and stored."""

    _couch_db_name: str | None = None
    """CouchDB database name, verified and stored."""

    _couch_db: Any | None = None
    """CouchDB database instance, initialized once and stored."""

    _collection_name_dict: dict[type, str] | None = None
    """Collection name dict, collection names are initialized once and stored."""

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
                # If neither is specified, use localhost with the default CouchDB port and credentials
                self.client_uri = "http://{db_username}:{db_password}@localhost:5984/"

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
        """Return true if the database contains no documents."""
        couch_db = self._get_couch_db()
        try:
            info = couch_db.info()
            return info.get("doc_count", 0) == 0
        except NotFound:
            return True

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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Query for all records in one call using $in operator
        keys_filter = self._get_couch_keys_filter(keys, dataset=dataset, tenant=tenant, collection_name=collection_name)
        # Add sort to the Mango query
        sort_list = None
        if sort_order != SortOrder.UNORDERED:
            sort_dir = "asc" if sort_order == SortOrder.ASC else "desc"
            sort_list = [{"_key": sort_dir}]
            keys_filter["sort"] = sort_list
        serialized_records = couch_db.find(keys_filter)

        # Apply sort to the iterable (as backup)
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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Create a query dictionary
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
            "_collection": collection_name,
        }

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # TODO: Filter by keys
        # serialized_primary_key = _KEY_SERIALIZER.serialize(key)
        # serialized_record = couch_db.get(f"{collection_name}:{serialized_primary_key}")

        # Build Mango query with sort, limit, and skip
        sort_list = None
        if sort_order != SortOrder.UNORDERED:
            sort_dir = "asc" if sort_order == SortOrder.ASC else "desc"
            sort_list = [{"_key": sort_dir}]

        mango_query = self._build_mango_query(query_dict, limit=limit, skip=skip, sort=sort_list)
        serialized_records = couch_db.find(mango_query)

        # Note: Sort, limit, and skip are handled in the Mango query, but we still apply them
        # to the results in case the query didn't handle them properly
        serialized_records = self._apply_sort(serialized_records, sort_field="_key", sort_order=sort_order)
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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(couch_db=couch_db, collection_name=collection_name, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
            "_collection": collection_name,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
        # TODO: Remove table fields

        # Convert op_* fields to CouchDB Mango query $* syntax
        query_dict = self._convert_op_fields_to_couch_syntax(query_dict)

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

        # Build Mango query with sort, limit, and skip
        sort_list = None
        if sort_order != SortOrder.UNORDERED:
            sort_dir = "asc" if sort_order == SortOrder.ASC else "desc"
            sort_list = [{"_key": sort_dir}]

        mango_query = self._build_mango_query(query_dict, limit=limit, skip=skip, sort=sort_list)
        serialized_records = couch_db.find(mango_query)

        # Note: Sort, limit, and skip are handled in the Mango query, but we still apply them
        # to the results in case the query didn't handle them properly
        serialized_records = self._apply_sort(serialized_records, sort_field="_key", sort_order=sort_order)
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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(couch_db=couch_db, collection_name=collection_name, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
            "_collection": collection_name,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
        # TODO: Remove table fields

        # Convert op_* fields to CouchDB Mango query $* syntax
        query_dict = self._convert_op_fields_to_couch_syntax(query_dict)

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

        # Use find to get the count
        mango_query = self._build_mango_query(query_dict)
        results = list(couch_db.find(mango_query))
        count = len(results)
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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # TODO: Provide a more performant implementation
        for record in records:
            # Serialize key
            serialized_key = _KEY_SERIALIZER.serialize(record.get_key())
            doc_id = f"{collection_name}:{serialized_key}"

            # Serialize record
            serialized_record = _RECORD_SERIALIZER.serialize(record)
            serialized_record["_id"] = doc_id
            serialized_record["_dataset"] = dataset
            serialized_record["_key"] = serialized_key
            serialized_record["_tenant"] = tenant
            serialized_record["_collection"] = collection_name

            if save_policy == SavePolicy.INSERT:
                # For INSERT, check if document exists first
                try:
                    existing = couch_db.get(doc_id)
                    raise RuntimeError(f"Document with id '{doc_id}' already exists")
                except NotFound:
                    couch_db.save(serialized_record)
            elif save_policy == SavePolicy.REPLACE:
                # For REPLACE, get existing _rev if document exists
                try:
                    existing = couch_db.get(doc_id)
                    serialized_record["_rev"] = existing["_rev"]
                except NotFound:
                    pass  # New document, no _rev needed
                couch_db.save(serialized_record)
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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Delete documents by their IDs
        for key in keys:
            serialized_key = _KEY_SERIALIZER.serialize(key)
            doc_id = f"{collection_name}:{serialized_key}"
            try:
                doc = couch_db.get(doc_id)
                # Verify dataset and tenant match
                if doc.get("_dataset") == dataset and doc.get("_tenant") == tenant:
                    couch_db.delete(doc)
            except NotFound:
                pass  # Document doesn't exist, skip

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

        # Get CouchDB database and collection name for the key type
        couch_db = self._get_couch_db()
        collection_name = self._get_collection_name(key_type=key_type)

        # Add index based on public fields of the query target type in the order of declaration from base to derived
        self._add_index(couch_db=couch_db, collection_name=collection_name, query_type=typeof(query))

        # Create query dict
        query_dict = {
            "_dataset": dataset,
            "_tenant": tenant,
            "_collection": collection_name,
        }

        # Serialize the query and update query dict
        query_dict.update(BootstrapSerializers.FOR_MONGO_QUERY.serialize(query))
        # TODO: Remove table fields

        # Convert op_* fields to CouchDB Mango query $* syntax
        query_dict = self._convert_op_fields_to_couch_syntax(query_dict)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query_target_type
        elif not issubclass(restrict_to, query_target_type):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {typename(type(self))}.delete_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Filter by restrict_to if specified
        self._apply_restrict_to(query_dict=query_dict, key_type=key_type, restrict_to=restrict_to)

        # Delete from DB
        mango_query = self._build_mango_query(query_dict)
        results = list(couch_db.find(mango_query))
        for doc in results:
            couch_db.delete(doc)

    def _drop_db_do_not_call_directly(self) -> None:
        """DO NOT CALL DIRECTLY, call drop_db() instead."""
        # Drop the database without possibility of recovery after
        # the preconditions check above to prevent unintended use
        server = self._get_couch_server()
        db_name = self._get_db_name()
        try:
            db = server.database(db_name)
            db.delete()
        except NotFound:
            pass  # Database doesn't exist, nothing to delete

    def close_connection(self) -> None:
        # TODO: Review the use of this method and when it is invoked
        # CouchDB connections are stateless, no explicit close needed
        pass

    def _convert_op_fields_to_couch_syntax(self, query_dict: dict[str, Any]) -> dict[str, Any]:
        """Convert op_* fields to CouchDB Mango query $* syntax recursively."""
        if not isinstance(query_dict, dict):
            return query_dict

        result = {}
        for key, value in query_dict.items():
            if key.startswith("op_"):
                # Convert op_* to $* syntax (CouchDB Mango queries use same $* syntax)
                couch_key = "$" + key[3:]  # Remove "op_" prefix
                result[couch_key] = value
            elif isinstance(value, dict):
                # Recursively convert nested dictionaries
                result[key] = self._convert_op_fields_to_couch_syntax(value)
            elif isinstance(value, list):
                # Recursively convert list items
                result[key] = [
                    self._convert_op_fields_to_couch_syntax(item) if isinstance(item, dict) else item for item in value
                ]
            else:
                # Keep other values as-is
                result[key] = value

        return result

    def _get_collection_name(self, key_type: type[KeyMixin]) -> str:
        """Get collection name for the specified key type."""
        if self._collection_name_dict is None:
            self._collection_name_dict = {}
        if (collection_name := self._collection_name_dict.get(key_type, None)) is None:
            # This also checks that the name of key_type has Key suffix
            assert TypeCheck.guard_key_type(key_type)

            # Get collection name
            key_type_name = typename(key_type)
            collection_name = key_type_name.removesuffix("Key")

            # Cache for reuse
            self._collection_name_dict[key_type] = collection_name
        return collection_name

    def _get_couch_server(self) -> Server:
        """Get CouchDB server object."""

        # TODO (Roman): Refactor. Consider removing _couch_server from instance-level fields
        if self._couch_server is None:

            cached_couch_server = _couch_server_dict.get(self.client_uri)
            if cached_couch_server is None:
                couch_server = Server(self.client_uri)
                self._couch_server = couch_server
                _couch_server_dict[self.client_uri] = couch_server
            else:
                self._couch_server = cached_couch_server

        return self._couch_server

    def _get_db_name(self) -> str:
        """For CouchDB, database name is db_id, perform validation before returning."""
        if self._couch_db_name is None:
            self._couch_db_name = self.db_id
            # Check for invalid characters in CouchDB name
            if False:  # TODO: !!!! Update for CouchDB and restore _INVALID_DB_NAME_REGEX.search(self._couch_db_name):
                raise RuntimeError(
                    f"CouchDB database name '{self._couch_db_name}' is not valid because it contains "
                    f"special characters from this list: '{_INVALID_DB_NAME_SYMBOLS_MSG}'"
                )

            # Check for maximum byte length of less than 249 (use Unicode bytes, not string chars to count)
            max_bytes = 249
            actual_bytes = len(self._couch_db_name.encode("utf-8"))
            if actual_bytes > max_bytes:
                raise RuntimeError(
                    f"CouchDB does not support database name '{self._couch_db_name}' because "
                    f"it has {actual_bytes} bytes, exceeding the maximum of {max_bytes}."
                )
        return self._couch_db_name

    def _get_couch_db(self) -> Any:
        """Get or create the CouchDB database object."""
        if self._couch_db is None:
            db_name = self._get_db_name()
            server = self._get_couch_server()
            try:
                self._couch_db = server.database(db_name)
            except NotFound:
                # Create database if it doesn't exist
                self._couch_db = server.create(db_name)
        return self._couch_db

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
        # Convert to list for CouchDB (since it doesn't have cursor-like objects)
        records_list = list(serialized_records)

        # Apply skip
        if skip is not None:
            if skip > 0:
                # Apply skip to list
                records_list = records_list[skip:]
            elif skip == 0:
                # We interpret skip=0 as not skipping, do nothing
                pass
            else:
                raise RuntimeError(f"Parameter skip={skip} is negative.")

        # Apply limit
        if limit is not None:
            if limit > 0:
                # Apply limit to list
                records_list = records_list[:limit]
            elif limit == 0:
                # Return no records
                return tuple()
            else:
                raise RuntimeError(f"Parameter limit={limit} is negative.")
        return iter(records_list)

    @classmethod
    def _apply_sort(cls, records: Iterable, sort_field: str, sort_order: SortOrder) -> Iterable:
        """Apply sorting to the records using the specified sort field and sort order."""
        if sort_order == SortOrder.UNORDERED:
            return records  # no sort applied

        # Convert to list for sorting
        records_list = list(records)

        if sort_order == SortOrder.ASC:
            records_list.sort(key=lambda x: x.get(sort_field, ""))
        elif sort_order == SortOrder.DESC:
            records_list.sort(key=lambda x: x.get(sort_field, ""), reverse=True)
        elif sort_order == SortOrder.INPUT:
            # Not implemented. Return unchanged records by default.
            pass
        else:
            raise ValueError(f"Unsupported SortOrder: {sort_order}")

        return iter(records_list)

    def _with_pruned_fields(
        self,
        record_dict: dict[str, Any],
        *,
        expected_dataset: str,
    ) -> dict[str, Any]:
        """Prune and validate fields that are not part of the serialized record data and return the same instance."""

        # Remove or pop and validate
        # Note: CouchDB uses _id and _rev, we keep _id for now but remove _rev
        if "_rev" in record_dict:
            del record_dict["_rev"]
        # Extract collection from _id if present (format: "collection:key")
        if "_id" in record_dict:
            _id = record_dict["_id"]
            if ":" in _id:
                # Remove collection prefix from _id
                record_dict["_id"] = _id.split(":", 1)[1]
        assert record_dict.pop("_dataset") == expected_dataset
        del record_dict["_key"]
        if "_collection" in record_dict:
            del record_dict["_collection"]

        return record_dict

    def _build_mango_query(self, selector: dict[str, Any], *, limit: int | None = None, skip: int | None = None, sort: list[dict[str, str]] | None = None) -> dict[str, Any]:
        """Build a CouchDB Mango query from selector and options."""
        query = {"selector": selector}
        if limit is not None:
            query["limit"] = limit
        if skip is not None:
            query["skip"] = skip
        if sort is not None:
            query["sort"] = sort
        return query

    def _get_couch_keys_filter(self, keys: Sequence[KeyMixin], *, dataset: str, tenant: str, collection_name: str) -> dict[str, Any]:
        """Get filter for loading records that match one of the specified keys."""
        serialized_keys = tuple(_KEY_SERIALIZER.serialize(key) for key in keys)
        # Build list of document IDs
        doc_ids = [f"{collection_name}:{key}" for key in serialized_keys]
        selector = {
            "_dataset": dataset,
            "_tenant": tenant,
            "_collection": collection_name,
            "_id": {"$in": doc_ids},
        }
        return self._build_mango_query(selector)

    def _add_index(
        self,
        *,
        couch_db: Any,
        collection_name: str,
        query_type: type,
    ) -> None:
        """Add index (design document) for the specified query_type."""
        if not self._query_types_with_index:
            # Create an empty set of query types for which the index has already been added
            self._query_types_with_index = set()
        if query_type not in self._query_types_with_index:

            # Build index fields list
            index_fields = ["_tenant", "_dataset"]
            # Populate query fields recursively
            self._populate_index(type_=query_type, result=index_fields)
            # Key is the last field in the index
            index_fields.append("_key")

            # Create design document for Mango index
            design_doc_id = f"_design/index_{typename(query_type).replace('.', '_')}"
            index_def = {
                "fields": [{"name": field, "type": "string"} for field in index_fields]
            }

            try:
                # Try to get existing design document
                design_doc = couch_db.get(design_doc_id)
                design_doc["indexes"] = design_doc.get("indexes", {})
                design_doc["indexes"][f"index_{typename(query_type)}"] = index_def
                couch_db.save(design_doc)
            except NotFound:
                # Create new design document
                design_doc = {
                    "_id": design_doc_id,
                    "indexes": {
                        f"index_{typename(query_type)}": index_def
                    }
                }
                couch_db.save(design_doc)

            # Add to the set of query types for which the index has already been added
            self._query_types_with_index.add(query_type)

    def _populate_index(
        self,
        *,
        type_: type,
        field_prefix: str | None = None,
        result: list[str],
    ) -> None:
        """
        Populate a flat list of field names for the specified type
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
                # Add a primitive or enum field (CouchDB indexes don't support direction in Mango, only in views)
                result.append(combined_field_prefix)
            elif is_data_key_or_record_type(field_type):
                # Add a data, key or record field
                self._populate_index(
                    type_=field_type,
                    field_prefix=combined_field_prefix,
                    result=result,
                )
            else:
                raise RuntimeError(f"Cannot create index for field type {typename(field_type)}.")
