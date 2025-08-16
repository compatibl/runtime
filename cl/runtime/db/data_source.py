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

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Self
from typing import Sequence
from typing import cast
from more_itertools import consume
from cl.runtime import Db
from cl.runtime import TypeCache
from cl.runtime.db.data_source_key import DataSourceKey
from cl.runtime.db.dataset import Dataset
from cl.runtime.db.dataset_key import DatasetKey
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.filter import Filter
from cl.runtime.db.filter_many import FilterMany
from cl.runtime.db.filter_by_type import FilterByType
from cl.runtime.db.filter_where import FilterWhere
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.resource_key import ResourceKey
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_type_binding import RecordTypeBinding
from cl.runtime.records.record_type_binding_query import RecordTypeBindingQuery
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.key_serializers import KeySerializers

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class DataSource(DataSourceKey, RecordMixin):
    """Rules for hierarchical lookup in multiple databases and datasets with data access control."""

    db: DbKey = required()
    """Database where lookup is performed (initialized to DB from the current context if not specified)."""

    dataset: DatasetKey = required()
    """Dataset within the database (initialized to the dataset from the current context if not specified)."""

    parent: DataSourceKey | None = None
    """Search in parent if not found in self, default data source is always added as ultimate parent (optional)."""

    included: list[ResourceKey] | None = None
    """Lookup here only the resources on this list, continue to parent for all other resources (optional)."""

    excluded: list[ResourceKey] | None = None
    """Continue to parent without lookup here for resources in this list (optional)."""

    designated: list[ResourceKey] | None = None
    """Lookup these resources only here, not in any child or parent (optional)."""

    def get_key(self) -> DataSourceKey:
        return DataSourceKey(data_source_id=self.data_source_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Load the database object, use default DB if not specified
        if self.db is None:
            self.db = Db.create()  # TODO: Move initialization code here?
        elif is_key(self.db):
            self.db = self.load_one(self.db)

        _LOGGER.info(f"Connected to DB type '{typename(self.db)}', db_id = '{self.db.db_id}'.")

        # Load dataset, use root dataset if not specified
        if self.dataset is None:
            self.dataset = Dataset.get_root()

        # TODO: These features are not yet supported
        if self.parent is not None:
            raise RuntimeError("DataSource.parent is not yet supported.")
        if self.included is not None:
            raise RuntimeError("DataSource.included is not yet supported.")
        if self.excluded is not None:
            raise RuntimeError("DataSource.excluded is not yet supported.")
        if self.designated is not None:
            raise RuntimeError("DataSource.designated is not yet supported.")

    def load_one(
        self,
        key_or_record: KeyProtocol,
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'key_or_record' is None or the record is not found in DB.

        Args:
            key_or_record: If a record, it will be returned without DB lookup
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
        """
        if key_or_record is not None:
            result = self.load_one_or_none(
                key_or_record,
                cast_to=cast_to,
                project_to=project_to,
            )
            if result is None:
                TypeCheck.is_key_or_record_type(type(key_or_record))
                if is_record(key_or_record):
                    key = key_or_record.get_key()
                else:
                    key = key_or_record
                key_str = KeySerializers.DELIMITED.serialize(key)
                cast_to_str = f"\nwhen loading type {typename(cast_to)}" if cast_to else ""
                raise RuntimeError(
                    f"Record not found for key {key_str}{cast_to_str}.\n"
                    f"Use 'load_one_or_none' method to return None instead of raising an error."
                )
            return result
        else:
            cast_to_str = f"\nwhen loading type {typename(cast_to)}" if cast_to else ""
            raise RuntimeError(
                f"Parameter 'key_or_record' is None for load_one method{cast_to_str}.\n"
                f"Use 'load_one_or_none' method to return None instead of raising an error."
            )

    def load_one_or_none(
        self,
        key_or_record: KeyProtocol | None,
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'key_or_record' is None or the record is not found in DB.

        Args:
            key_or_record: If a record, it will be returned without DB lookup
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
        """
        result = self.load_many_or_none(
            [key_or_record],
            cast_to=cast_to,
            project_to=project_to,
        )
        if len(result) == 1:
            return result[0]
        else:
            raise RuntimeError(f"DataSource.load_many returned {len(result)} records when one was requested.")

    def load_many(
        self,
        records_or_keys: Sequence[TRecord | KeyProtocol],
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.INPUT,
    ) -> Sequence[TRecord]:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Note:
            - Raise an error if records_or_keys param is None elements or has None elements
            - Raise an error if any of the records are not found

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """
        # Check that the argument is not None and there are no elements that are None
        TypeCheck.is_key_or_record_sequence(records_or_keys)

        # Delegate to load_many_or_none method
        result = self.load_many_or_none(
            records_or_keys,
            cast_to=cast_to,
            project_to=project_to,
            sort_order=sort_order,
        )

        # Perform checks and return
        TypeCheck.is_record_sequence(result)
        return result

    def load_many_or_none(
        self,
        records_or_keys: Sequence[TRecord | KeyProtocol | None] | None,
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.INPUT,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Note:
            - Return None for any elements of records_or_keys that are None, or for which the record is not found
            - The result is None if records_or_keys param is None

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """
        assert TypeCheck.is_key_or_record_sequence_or_none(records_or_keys)

        # Pass through None or empty
        if not records_or_keys:
            return records_or_keys

        # Perform these checks if cast_to is specified
        if cast_to is not None:
            # Check that the keys in the input list have the same type as cast_to.get_key_type()
            key_type = cast_to.get_key_type()
            invalid_keys = [x for x in records_or_keys if is_key(x) and not isinstance(x, key_type)]
            if len(invalid_keys) > 0:
                invalid_keys_str = "\n".join(str(x) for x in invalid_keys)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following keys\n"
                    f"whose type is not the same as the key type {typename(key_type)}\n"
                    f"of the cast_to parameter {typename(cast_to)}:\n{invalid_keys_str}"
                )
            # Check that the records in the input list are derived from cast_to
            invalid_records = [x for x in records_or_keys if is_record(x) and not isinstance(x, cast_to)]
            if len(invalid_records) > 0:
                invalid_records_str = "\n".join(str(x) for x in invalid_records)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following records\n"
                    f"that are not derived from the cast_to parameter {typename(cast_to)}:\n{invalid_records_str}"
                )

        # The list of keys to load, skip None and records
        keys_to_load = [x for x in records_or_keys if is_key(x)]

        # Group keys by table
        keys_to_load_grouped_by_key_type = self._group_inputs_by_key_type(keys_to_load)

        # Get records from DB, the result is unsorted and grouped by table
        loaded_records_grouped_by_key_type = [
            self._get_db().load_many(key_type, keys_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, keys_for_key_type in keys_to_load_grouped_by_key_type.items()
        ]

        # Concatenated list
        loaded_records = [item for sublist in loaded_records_grouped_by_key_type for item in sublist]
        serialized_loaded_keys = [KeySerializers.TUPLE.serialize(x.get_key()) for x in loaded_records]

        # Create a dictionary with pairs consisting of serialized key (after normalization) and the record for this key
        loaded_records_dict = {k: v for k, v in zip(serialized_loaded_keys, loaded_records)}

        # Populate the result with records loaded using input keys, pass through None and input records
        result = tuple(
            loaded_records_dict.get(KeySerializers.TUPLE.serialize(x), None) if is_key(x) else x
            for x in records_or_keys
        )

        # Cast to cast_to if specified, pass through None
        if cast_to is not None:
            result = tuple(CastUtil.cast_or_none(cast_to, x) for x in result)
        return result

    def load_type(
        self,
        restrict_to: type[TRecord],
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records of 'restrict_to' type and its subtypes.

        Args:
            restrict_to: The query will return only this type and its subtypes
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        # Delegate to load_all method with 'restrict_to' parameter
        return self._get_db().load_all(
            restrict_to.get_key_type(),
            dataset=self.dataset.dataset_id,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            sort_order=sort_order,
            limit=limit,
            skip=skip,
        )

    def load_all(
        self,
        key_type: type[KeyProtocol],
        *,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records for the specified key type.

        Args:
            key_type: Key type determines the database table
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only this type and its subtypes
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        TypeCheck.is_key_type(key_type)

        return self._get_db().load_all(
            key_type=key_type,
            dataset=self.dataset.dataset_id,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            sort_order=sort_order,
            limit=limit,
            skip=skip,
        )

    def load_filter(
        self,
        filter_: Filter,
        *,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.ASC,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load records selected by the specified filter.

        Args:
            filter_: Filter used to select the records to load
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only this type and its subtypes
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        assert isinstance(filter_, Filter)

        if isinstance(filter_, FilterWhere):

            # Load using the query stored in the filter
            return self.load_where(
                filter_.query,
                cast_to=cast_to,
                restrict_to=restrict_to,
                project_to=project_to,
                sort_order=sort_order,
                limit=limit,
                skip=skip,
            )
        elif isinstance(filter_, FilterByType):

            # Perform checks for parameters that cannor be combined with FilterByType type
            if restrict_to is not None:
                raise RuntimeError("Param 'restrict_to' cannot be combined with FilterMany type.")

            # Convert type name to type
            record_type = TypeCache.from_type_name(filter_.record_type_name)

            # Load using the type stored in the filter as restrict_to parameter
            return self.load_type(
                restrict_to=record_type,  # noqa
                cast_to=cast_to,
                project_to=project_to,
                sort_order=sort_order,
                limit=limit,
                skip=skip,
            )
        elif isinstance(filter_, FilterMany):

            # Perform checks for parameters that cannor be combined with FilterMany type
            if restrict_to is not None:
                raise RuntimeError("Param 'restrict_to' cannot be combined with FilterMany type.")
            if limit is not None:
                raise RuntimeError("Param 'limit' cannot be combined with FilterMany type.")
            if skip is not None:
                raise RuntimeError("Param 'skip' cannot be combined with FilterMany type.")

            # Load using the keys stored in the filter
            return self.load_many(
                filter_.keys,  # noqa
                cast_to=cast_to,
                project_to=project_to,
                sort_order=sort_order,
            )
        else:
            raise RuntimeError(f"Filter type {typename(filter_)} not supported by the data source.")

    def load_where(
        self,
        query: QueryMixin,
        *,
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
            query: Contains query conditions to match
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only this type and its subtypes
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return self._get_db().load_where(
            query,
            dataset=self.dataset.dataset_id,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            sort_order=sort_order,
            limit=limit,
            skip=skip,
        )

    def count_where(
        self,
        query: QueryMixin,
        *,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query using the current context's DB.

        Args:
            query: Contains query conditions to match
            restrict_to: The query will return only this type and its subtypes
        """
        return self._get_db().count_where(
            query,
            dataset=self.dataset.dataset_id,
            restrict_to=restrict_to,
        )

    def save_one(
        self,
        record: RecordProtocol,
    ) -> None:
        """Save the specified record to storage, replace rather than update individual fields if it exists."""
        self.save_many([record])

    def save_many(
        self,
        records: Sequence[RecordProtocol],
    ) -> None:
        """Save the specified records to storage, replace rather than update individual fields for those that exist."""
        TypeCheck.is_record_sequence(records)

        # Do nothing if empty but error on None
        if len(records) == 0:
            return

        # Group records by key type
        records_grouped_by_key_type = self._group_inputs_by_key_type(records)

        # Save records for each key type
        [
            self._get_db().save_many(key_type, records_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, records_for_key_type in records_grouped_by_key_type.items()
        ]

    def delete_one(
        self,
        key: KeyProtocol,
    ) -> None:
        """Delete record for the specified key in object, tuple or string format (no error if not found)."""
        return self.delete_many([key])

    def delete_many(
        self,
        keys: Sequence[KeyProtocol],
    ) -> None:
        """Delete records for the specified keys in object, tuple or string format (no error if not found)."""
        assert TypeCheck.is_key_sequence(keys)

        # Do nothing if empty but error on None
        if len(keys) == 0:
            return

        # Group keys by key type
        keys_grouped_by_key_type = self._group_inputs_by_key_type(keys)

        # Perform deletion for every key type
        [
            self._get_db().delete_many(key_type, records_for_key_type, dataset=self.dataset.dataset_id)
            for key_type, records_for_key_type in keys_grouped_by_key_type.items()
        ]

    def get_bindings(self) -> tuple[RecordTypeBinding, ...]:
        """Return record type bindings in alphabetical order of key type name followed by record type name."""

        # Load from DB as cache may be out of date
        bindings = self.load_type(RecordTypeBinding)
        # Sort bindings by key type name first and then by record type in alphabetical order
        return tuple(sorted(bindings, key=lambda x: (x.key_type_name, x.record_type_name)))

    def get_key_type_names(self) -> tuple[str, ...]:
        """Return stored key type names in alphabetical order of PascalCase format."""

        # Load from DB as cache may be out of date
        bindings = self.load_type(RecordTypeBinding)
        # Convert to set to remove duplicates, sort in alphabetical order, convert back to tuple
        return tuple(sorted(set(binding.key_type_name for binding in bindings)))

    def get_record_type_names(self, *, key_type_name: str | None = None) -> tuple[str, ...]:
        """
        Return PascalCase record type names in alphabetical order for records stored in this DB,
        with optional filtering by key type name.

        Returns:
            Tuple of PascalCase record type names in alphabetical order or an empty tuple.

        Args:
            key_type_name: Filter the result by key type name in PascalCase format if specified (optional)
        """

        # Load from DB as cache may be out of date
        query = RecordTypeBindingQuery(key_type_name=key_type_name).build()
        bindings = self.load_where(query, cast_to=RecordTypeBinding)

        # Sort in alphabetical order of record_type (not the same as query sort order) and convert to tuple
        return tuple(sorted(binding.record_type_name for binding in bindings))

    def get_common_base_record_type_name(self, *, key_type_name: str) -> str:
        """
        Return the name of the common type for all records stored for this key type name, error if no such records.

        Args:
            key_type_name: Key type name in PascalCase format (required).
        """

        if not key_type_name:
            raise RuntimeError("Key type name is required in get_common_base_record_type_name method.")

        # Get record type names stored for this key type name
        bound_type_names = self.get_record_type_names(key_type_name=key_type_name)

        if bound_type_names:
            # Find the common base name
            result = TypeCache.get_common_base_type_name(
                types_or_names=bound_type_names,
                type_kind=TypeKind.RECORD,
            )
            return result
        else:
            # Empty bound_type_names can only occur if key_type_name is not stored, raise an error
            raise RuntimeError(f"Table {key_type_name} is empty.")

    def _get_db(self) -> Db:
        """Cast db key type to record type, the record is already loaded by the __init method."""
        return cast(Db, self.db)

    def _get_parent(self) -> Self:
        """Cast parent key types to record type, the record is already loaded by the __init method."""
        return cast(Self, self.parent)

    @classmethod
    def _group_inputs_by_key_type(
        cls, inputs: Sequence[RecordProtocol | KeyProtocol | None]
    ) -> dict[type[KeyProtocol], Sequence[RecordProtocol | KeyProtocol | None]]:
        """Group inputs by key type, skipping sequence elements that are None."""
        result = defaultdict(list)
        consume(result[x.get_key_type()].append(x) for x in inputs if x is not None)
        return result
