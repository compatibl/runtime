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
from cl.runtime.db.data_source_key import DataSourceKey
from cl.runtime.db.dataset import Dataset
from cl.runtime.db.dataset_key import DatasetKey
from cl.runtime.db.db import Db
from cl.runtime.db.db_key import DbKey
from cl.runtime.db.filter import Filter
from cl.runtime.db.filter_by_query import FilterByQuery
from cl.runtime.db.filter_by_type import FilterByType
from cl.runtime.db.filter_many import FilterMany
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.resource_key import ResourceKey
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.record_type_presence import RecordTypePresence
from cl.runtime.records.record_type_presence_query import RecordTypePresenceQuery
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typeof
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_hint import TypeHint
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

    _pending_deletions: list[KeyMixin] | None = None
    """Keys that will be deleted on commit."""

    _pending_insertions: list[RecordMixin] | None = None
    """Records that will be inserted on commit."""

    _pending_replacements: list[RecordMixin] | None = None
    """Records that will be replaced on commit."""

    def get_key(self) -> DataSourceKey:
        return DataSourceKey(data_source_id=self.data_source_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Use globally unique UUIDv7-based timestamp if not specified
        if self.data_source_id is None:
            self.data_source_id = Timestamp.create()

        # Load the database object, use default DB if not specified
        if self.db is None:
            self.db = Db.create()  # TODO: Move initialization code here?
        elif is_key_type(type(self.db)):
            self.db = self.load_one(self.db)

        _LOGGER.info(f"Connected to DB type '{typename(type(self.db))}', db_id = '{self.db.db_id}'.")

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

        # Initialize the list of pending deletes and inserts
        self._clear_pending_operations()

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        if self._pending_deletions:
            raise RuntimeError(
                f"The list of pending deletions is not empty on __enter__ for data_source_id={self.data_source_id}.\n"
                f"Call commit() or rollback() before reusing the data source instance in a different 'with' clause."
            )
        if self._pending_insertions:
            raise RuntimeError(
                f"The list of pending insertions is not empty on __enter__ for data_source_id={self.data_source_id}.\n"
                f"Call commit() or rollback() before reusing the data source instance in a different 'with' clause."
            )
        if self._pending_replacements:
            raise RuntimeError(
                f"The list of pending replacements is not empty on __enter__ for data_source_id={self.data_source_id}.\n"
                f"Call commit() or rollback() before reusing the data source instance in a different 'with' clause."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        if exc_type is None:
            # Commit if there is no exception
            self.commit()
        else:
            # Rollback if there is an exception and let the exception propagate (do not suppress)
            self.rollback()

    def load_one(
        self,
        key_or_record: KeyMixin,
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
                assert TypeCheck.guard_key_or_record_type(type(key_or_record))
                if is_record_type(type(key_or_record)):
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
        key_or_record: KeyMixin | None,
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
        records_or_keys: Sequence[TRecord | KeyMixin],
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.INPUT,
    ) -> Sequence[TRecord]:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup).

        Note:
            - Raise an error if records_or_keys param is None or has None elements
            - Raise an error if any of the records are not found

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """
        # Check that the argument is not None and there are no elements that are None
        assert TypeCheck.guard_key_or_record_sequence(records_or_keys)

        # Delegate to load_many_or_none method
        result = self.load_many_or_none(
            records_or_keys,
            cast_to=cast_to,
            project_to=project_to,
            sort_order=sort_order,
        )

        # Perform checks and return
        assert TypeCheck.guard_record_sequence(result)
        return result

    def load_many_or_none(
        self,
        records_or_keys: Sequence[TRecord | KeyMixin | None] | None,
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        sort_order: SortOrder = SortOrder.INPUT,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup).

        Note:
            - Return None for any elements of records_or_keys that are None, or for which the record is not found
            - The result is None if records_or_keys param is None

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
        """
        assert TypeCheck.guard_key_or_record_sequence_or_none(records_or_keys)

        # Pass through None or empty
        if not records_or_keys:
            return records_or_keys

        # TODO: Delegate to TypeCheck
        if cast_to is not None:
            # Check that the keys in the input list have the same type as cast_to.get_key_type()
            key_type = cast_to.get_key_type()
            invalid_keys = [x for x in records_or_keys if is_key_type(type(x)) and not isinstance(x, key_type)]
            if len(invalid_keys) > 0:
                invalid_keys_str = "\n".join(str(x) for x in invalid_keys)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following keys\n"
                    f"whose type is not the same as the key type {typename(key_type)}\n"
                    f"of the cast_to parameter {typename(cast_to)}:\n{invalid_keys_str}"
                )
            # Check that the records in the input list are derived from cast_to
            invalid_records = [x for x in records_or_keys if is_record_type(type(x)) and not isinstance(x, cast_to)]
            if len(invalid_records) > 0:
                invalid_records_str = "\n".join(str(x) for x in invalid_records)
                raise RuntimeError(
                    f"Parameter 'records_or_keys' of a load method in DataSource includes the following records\n"
                    f"that are not derived from the cast_to parameter {typename(cast_to)}:\n{invalid_records_str}"
                )

        # The list of keys to load, skip None and records
        keys_to_load = [x for x in records_or_keys if is_key_type(type(x))]

        # Group keys by table
        keys_to_load_grouped_by_key_type = self._group_inputs_by_key_type(keys_to_load)

        # Select sort order to use for the DB call
        if sort_order == SortOrder.INPUT:
            # For INPUT, use UNORDERED for the DB call as
            # the result will be matched to inputs after loading
            db_sort_order = SortOrder.UNORDERED
        else:
            db_sort_order = sort_order

        # Get records from DB, the result is unsorted and grouped by table
        loaded_records_grouped_by_key_type = [
            self._get_db().load_many(
                key_type,
                keys_for_key_type,
                dataset=self.dataset.dataset_id,
                project_to=project_to,
                sort_order=db_sort_order,
            )
            for key_type, keys_for_key_type in keys_to_load_grouped_by_key_type.items()
        ]

        # Concatenated list
        loaded_records = [item for sublist in loaded_records_grouped_by_key_type for item in sublist]
        serialized_loaded_keys = [KeySerializers.TUPLE.serialize(x.get_key()) for x in loaded_records]

        # Create a dictionary with pairs consisting of serialized key (after normalization) and the record for this key
        loaded_records_dict = {k: v for k, v in zip(serialized_loaded_keys, loaded_records)}

        # Populate the result with records loaded using input keys, pass through None and input records
        result = tuple(
            loaded_records_dict.get(KeySerializers.TUPLE.serialize(x), None) if is_key_type(type(x)) else x
            for x in records_or_keys
        )

        # Cast to cast_to if specified, pass through None
        if cast_to is not None:
            result = tuple(CastUtil.cast_or_none(cast_to, x) for x in result)
        return result

    def load_by_type(
        self,
        record_type: type[TRecord],
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
            record_type: Load only this type and its subtypes
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        # Delegate to load_all method with 'restrict_to' parameter set to record_type
        return self.load_all(
            record_type.get_key_type(),
            cast_to=cast_to,
            restrict_to=record_type,
            project_to=project_to,
            sort_order=sort_order,
            limit=limit,
            skip=skip,
        )

    def load_all(
        self,
        key_type: type[KeyMixin],
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
            restrict_to: Include only this type and its subtypes, skip other types
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by key fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        assert TypeCheck.guard_key_type(key_type)

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

    def load_by_filter(
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
            restrict_to: Include only this type and its subtypes, skip other types
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        assert isinstance(filter_, Filter)

        if isinstance(filter_, FilterByQuery):

            # Load using the query stored in the filter
            return self.load_by_query(
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
            record_type = TypeInfo.from_type_name(filter_.record_type_name)

            # Load using the type stored in the filter as restrict_to parameter
            return self.load_by_type(
                record_type=record_type,  # noqa
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
            raise RuntimeError(f"Filter type {typename(type(filter_))} not supported by the data source.")

    def load_by_query(
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
            restrict_to: Include only this type and its subtypes, skip other types
            project_to: Use some or all fields from the stored record to create and return instances of this type
            sort_order: Sort by query fields in the specified order, reversing for fields marked as DESC
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return self._get_db().load_by_query(
            query,
            dataset=self.dataset.dataset_id,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            sort_order=sort_order,
            limit=limit,
            skip=skip,
        )

    def count_by_query(
        self,
        query: QueryMixin,
        *,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query.

        Args:
            query: Contains query conditions to match
            restrict_to: Include only this type and its subtypes, skip other types
        """
        return self._get_db().count_by_query(
            query,
            dataset=self.dataset.dataset_id,
            restrict_to=restrict_to,
        )

    def insert_one(
        self,
        record: RecordMixin,
        *,
        commit: bool,
    ) -> None:
        """
        Insert the specified record to DB, error if a record exists for the same key.

        Notes:
            - DB is written to when commit() is called, or on data source context exit without exception
            - Pending commits are cancelled when rollback() is called, or on data source context exit with exception

        Args:
            record: Record to be inserted
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
        """
        self._save_many([record], commit=commit, save_policy=SavePolicy.INSERT)

    def insert_many(
        self,
        records: RecordMixin | Sequence[RecordMixin],
        *,
        commit: bool,
    ) -> None:
        """
        Insert the specified records to DB, error if any records exist for the same key.

        Notes:
            - DB is written to when commit() is called, or on data source context exit without exception
            - Pending commits are cancelled when rollback() is called, or on data source context exit with exception

        Args:
            records: A sequence of records which may have different key types
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
        """
        self._save_many(records, commit=commit, save_policy=SavePolicy.INSERT)

    def replace_one(
        self,
        record: RecordMixin,
        *,
        commit: bool,
    ) -> None:
        """
        Insert or replace (if it exists) the specified record.

        Notes:
            - DB is written to when commit() is called, or on data source context exit without exception
            - Pending commits are cancelled when rollback() is called, or on data source context exit with exception

        Args:
            record: Record to be saved
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
        """
        self._save_many([record], commit=commit, save_policy=SavePolicy.REPLACE)

    def replace_many(
        self,
        records: RecordMixin | Sequence[RecordMixin],
        *,
        commit: bool,
    ) -> None:
        """
        Insert or replace (if they exist) the specified records.

        Notes:
            - DB is written to when commit() is called, or on data source context exit without exception
            - Pending commits are cancelled when rollback() is called, or on data source context exit with exception

        Args:
            records: A sequence of records which may have different key types
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
        """
        self._save_many(records, commit=commit, save_policy=SavePolicy.REPLACE)

    def delete_one(
        self,
        key: KeyMixin,
        *,
        commit: bool,
    ) -> None:
        """Delete record for the specified key in object, tuple or string format (no error if not found)."""
        return self.delete_many([key], commit=commit)

    def delete_many(
        self,
        keys: Sequence[KeyMixin],
        *,
        commit: bool,
    ) -> None:
        """
        Delete the specified key or key sequence from DB on commit.

        Notes:
            - Records are deleted when commit() is called, or on data source context exit if exception is not raised
            - Pending deletions are cancelled when rollback() is called, or on data source context exit under exception

        Args:
            keys: A single key or a sequence of keys which may have different types
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
        """
        assert TypeCheck.guard_key_sequence(keys)

        # Do nothing if empty but error on None
        if len(keys) == 0:
            return

        # Add to the list of pending deletes
        self._pending_deletions.extend(keys)

        # Commit immediately if commit parameter is True
        if commit:
            self.commit()

    def commit(self) -> None:
        """Commit all pending saves and deletes, operations will not be retried in case of an error during commit."""

        # Exit early if there are no pending operations
        if not self._has_pending_operations():
            return

        try:
            # Ensure no key collisions within the deletions, insertions and replacements lists
            pending_keys = self._pending_deletions + [
                x.get_key()
                for x in (self._pending_insertions + self._pending_replacements)
            ]
            serialized_pending_keys = [
                KeySerializers.DELIMITED.serialize(x, type_hint=TypeHint.for_type(KeyMixin))
                for x in pending_keys
            ]
            # Dictionary of keys indexed by their serialization into tuple
            seen_pending_keys = defaultdict(list)
            for x in serialized_pending_keys:
                seen_pending_keys[x].append(True)
            # Keep only when there is more than one
            duplicate_pending_keys = {k: v for k, v in seen_pending_keys.items() if len(v) > 1}
            if duplicate_pending_keys:
                duplicate_pending_keys_msgs = [f"  - {x}" for x in duplicate_pending_keys]
                duplicate_pending_keys_str = "\n".join(msg for msg in duplicate_pending_keys_msgs)
                raise RuntimeError(
                    f"The following keys are present more than once in the list of\n"
                    f"pending commit operations (deletions, insertions and replacements)\n"
                    f"for data_source_id={self.data_source_id}:\n"
                    f"{duplicate_pending_keys_str}"
                )

            # Records to be inserted or replaced, with duplicates removed
            record_types = set(typeof(x) for x in (self._pending_insertions + self._pending_replacements))
            if record_types:
                # Add presence records without checking if they are already present, as
                # it is faster to save all records than to check which already exist
                record_types.add(RecordTypePresence)
                record_type_presences = tuple(
                    RecordTypePresence(record_type=x, key_type=x.get_key_type()).build() for x in record_types
                )
                self._pending_replacements.extend(record_type_presences)

            # Invoke delete_many for all pending deletes
            if self._pending_deletions:
                [
                    # Delete first
                    self._get_db().delete_many(key_type, records_for_key_type, dataset=self.dataset.dataset_id)
                    for key_type, records_for_key_type in self._group_inputs_by_key_type(self._pending_deletions).items()
                ]

            # Invoke insert_many for all pending inserts
            if self._pending_insertions:
                for key_type, records_for_key_type in self._group_inputs_by_key_type(self._pending_insertions).items():
                    # Insert next
                    self._get_db().save_many(
                        key_type,
                        records_for_key_type,
                        dataset=self.dataset.dataset_id,
                        save_policy=SavePolicy.INSERT,
                    )
            if self._pending_replacements:
                for key_type, records_for_key_type in self._group_inputs_by_key_type(self._pending_replacements).items():
                    # Replace last
                    self._get_db().save_many(
                        key_type,
                        records_for_key_type,
                        dataset=self.dataset.dataset_id,
                        save_policy=SavePolicy.REPLACE,
                    )
        except Exception as e:
            # Clear all pending operations before propagating
            self._clear_pending_operations()
            # Rethrow to propagate
            raise e
        else:
            # Clear all pending operations before exiting
            self._clear_pending_operations()

    def rollback(self) -> None:
        """Cancel all pending deletes, inserts and replacements."""
        self._clear_pending_operations()

    def _has_pending_operations(self) -> bool:
        """Return True if there are pending operations."""
        return bool(self._pending_deletions) or bool(self._pending_insertions) or bool(self._pending_replacements)

    def _clear_pending_operations(self) -> None:
        """Cancel all pending operations."""
        self._pending_deletions = []
        self._pending_insertions = []
        self._pending_replacements = []

    def get_key_types(self) -> tuple[type, ...]:
        """Return stored key types in alphabetical order of type name."""
        # Load from DB as cache may be out of date, eliminate duplicates
        key_types = set(x.key_type for x in self.load_by_type(RecordTypePresence))
        # Sort in alphabetical order of type name
        return tuple(sorted(key_types, key=lambda x: typename(x.get_key_type())))

    def get_record_types(self, *, key_type: type | None = None) -> tuple[type, ...]:
        """
        Return record types in alphabetical order of type name for records stored in this DB,
        with optional filtering by key type.

        Args:
            key_type: Filter the result by key type if specified (optional)
        """

        # Always load from DB as cache may be out of date
        query = RecordTypePresenceQuery(key_type=key_type).build()
        record_type_presences = [x.record_type for x in self.load_by_query(query, cast_to=RecordTypePresence)]

        # Sort in alphabetical order of record_type (not the same as query sort order)
        return tuple(sorted(record_type_presences, key=lambda x: typename(x)))

    def get_common_base_record_type(self, *, key_type: type) -> type:
        """Return the common type for all records stored for this key type, error if no such records."""

        # Get record types stored for this key type
        record_types = self.get_record_types(key_type=key_type)

        if record_types:
            # If at least one record type is present, find the common base
            return TypeInfo.get_common_base_type(types=record_types)
        else:
            # Empty record_types means no records stored, raise an error
            raise RuntimeError(f"Table {typename(key_type)} is empty.")

    def _get_db(self) -> Db:
        """Cast db key type to record type, the record is already loaded by the __init method."""
        return cast(Db, self.db)

    def _get_parent(self) -> Self:
        """Cast parent key types to record type, the record is already loaded by the __init method."""
        return cast(Self, self.parent)

    @classmethod
    def _group_inputs_by_key_type(
        cls, inputs: Sequence[RecordMixin | KeyMixin | None]
    ) -> dict[type[KeyMixin], Sequence[RecordMixin | KeyMixin | None]]:
        """Group inputs by key type, skipping sequence elements that are None."""
        result = defaultdict(list)
        consume(result[x.get_key_type()].append(x) for x in inputs if x is not None)
        return result

    def _save_many(
        self,
        records: Sequence[RecordMixin],
        *,
        commit: bool,
        save_policy: SavePolicy,
    ) -> None:
        """
        Save the specified record or record sequence, insert vs. replace behavior is governed by save_policy.

        Notes:
            - Records are saved when commit() is called, or on data source context exit if exception is not raised
            - Pending saves are cancelled when rollback() is called, or on data source context exit under exception

        Args:
            records: A sequence of records which may have different key types
            commit: If True, commit() is called immediately after which will also commit other pending saves and deletes
            save_policy: Insert vs. replace policy, partial update is not included due to design considerations
        """
        assert TypeCheck.guard_record_sequence(records)
        assert NoneChecks.guard_not_none(save_policy)

        # Do nothing if empty but error on None
        if len(records) == 0:
            return

        if save_policy == SavePolicy.INSERT:
            # Add to the list of pending inserts
            self._pending_insertions.extend(records)
        elif save_policy == SavePolicy.REPLACE:
            # Add to the list of pending replacements
            self._pending_replacements.extend(records)
        else:
            ErrorUtil.enum_value_error(save_policy, SavePolicy)

        # Commit immediately if commit parameter is True
        if commit:
            self.commit()
