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

from typing import Sequence

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_singleton_key
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.TUPLE
"""Serializer for keys used in cache lookup."""


class DataContext:
    """Methods to access the active data source context."""

    @classmethod
    def get_bindings(cls) -> tuple[TableBinding, ...]:
        """
        Return table to record type bindings in alphabetical order of table name followed by record type name.
        More than one table can exist for the same record type and vice versa.
        """
        return active(DataSource).get_bindings()

    @classmethod
    def get_tables(cls) -> tuple[str, ...]:
        """Return DB table names in alphabetical order of PascalCase format."""
        return active(DataSource).get_tables()

    @classmethod
    def get_record_type_names(cls) -> tuple[str, ...]:
        """
        Return PascalCase record type names in alphabetical order for records stored in this DB.
        More than one table can exist for the same record type.
        """
        return active(DataSource).get_record_type_names()

    @classmethod
    def get_bound_tables(cls, *, record_type: type[RecordProtocol] | str) -> tuple[str, ...]:
        """
        Return PascalCase tables for the specified record type or name in alphabetical order.

        Args:
            record_type: Record type or type name for which the tables are returned.
        """
        return active(DataSource).get_bound_tables(record_type=record_type)

    @classmethod
    def get_bound_key_type(cls, *, table: str) -> type:
        """
        Key type for the specified table, the table must exist.

        Args:
            table: Table name in PascalCase format.
        """
        return active(DataSource).get_bound_key_type(table=table)

    @classmethod
    def get_bound_record_type_names(cls, *, table: str) -> tuple[str, ...]:
        """
        Return PascalCase record type names in alphabetical order stored in the specified table.

        Args:
            table: Table name in PascalCase format.
        """
        return active(DataSource).get_bound_record_type_names(table=table)

    @classmethod
    def get_allowed_record_type_names(cls, *, table: str) -> tuple[str, ...]:
        """
        Record type names that may be stored in the specified table, the table must exist.

        Args:
            table: Table name in PascalCase format.
        """
        return active(DataSource).get_allowed_record_type_names(table=table)

    @classmethod
    def get_lowest_bound_record_type_name(cls, *, table: str) -> str:
        """
        Return the name of the lowest common type for the record types bound to the table, error if the table is empty.

        Args:
            table: Table name in PascalCase format.
        """
        return active(DataSource).get_lowest_bound_record_type_name(table=table)

    @classmethod
    def load_one(
        cls,
        record_or_key: TKey,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Error message if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return active(DataSource).load_one(
            record_or_key,
            cast_to=cast_to,
        )

    @classmethod
    def load_one_or_none(
        cls,
        record_or_key: TKey | None,
        *,
        cast_to: type[TRecord] | None = None,
    ) -> TRecord | None:
        """
        Load a single record using a key (if a record is passed instead of a key, it is returned without DB lookup).
        Return None if 'record_or_key' is None or the record is not found in DB.

        Args:
            record_or_key: Record (returned without lookup), key, or, if there is only one primary key field, its value
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return active(DataSource).load_one_or_none(
            record_or_key,
            cast_to=cast_to,
        )

    @classmethod
    def load_many(
        cls,
        records_or_keys: Sequence[TRecord | TKey | None] | None,
        *,
        cast_to: type[TRecord] | None = None,
    ) -> Sequence[TRecord | None] | None:
        """
        Load records using a list of keys (if a record is passed instead of a key, it is returned without DB lookup),
        the result must have the same order as 'records_or_keys'.

        Args:
            records_or_keys: Records (returned without lookup) or keys in object, tuple or string format
            cast_to: Perform runtime checked cast to this class if specified, error if not a subtype
        """
        return active(DataSource).load_many(
            records_or_keys,
            cast_to=cast_to,
        )

    @classmethod
    def load_type(
        cls,
        restrict_to: type[TRecord],
        *,
        cast_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records of 'restrict_to' type and its subtypes from all tables where they are stored.

        Args:
            restrict_to: The query will return only this type and its subtypes
            cast_to: Cast the result to this type (error if not a subtype)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return active(DataSource).load_type(
            restrict_to,
            cast_to=cast_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    @classmethod
    def load_table(
        cls,
        table: str,
        *,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load all records from the specified table.

        Args:
            table: The table from which the records are loaded
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return active(DataSource).load_table(
            table,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    @classmethod
    def load_where(
        cls,
        query: QueryMixin,
        *,
        cast_to: type[TRecord] | None = None,
        restrict_to: type[TRecord] | None = None,
        project_to: type[TRecord] | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> tuple[TRecord, ...]:
        """
        Load records that match the specified query.

        Args:
            query: Contains query conditions to match
            cast_to: Cast the result to this type (error if not a subtype)
            restrict_to: The query will return only the subtypes of this type (defaults to the query target type)
            project_to: Use some or all fields from the stored record to create and return instances of this type
            limit: Maximum number of records to return (for pagination)
            skip: Number of records to skip (for pagination)
        """
        return active(DataSource).load_where(
            query,
            cast_to=cast_to,
            restrict_to=restrict_to,
            project_to=project_to,
            limit=limit,
            skip=skip,
        )

    @classmethod
    def count_where(
        cls,
        query: QueryMixin,
        *,
        restrict_to: type | None = None,
    ) -> int:
        """
        Return the count of records that match the specified query using the current context's DB.

        Args:
            query: Contains query conditions to match
            restrict_to: Count only the subtypes of this type (defaults to the query target type)
        """
        return active(DataSource).count_where(
            query,
            restrict_to=restrict_to,
        )

    @classmethod
    def save_one(
        cls,
        record: RecordProtocol,
    ) -> None:
        """Save the specified record to storage, replace rather than update individual fields if it exists."""
        active(DataSource).save_one(
            record,
        )

    @classmethod
    def save_many(
        cls,
        records: Sequence[RecordProtocol],
    ) -> None:
        """Save the specified records to storage, replace rather than update individual fields for those that exist."""
        active(DataSource).save_many(
            records,
        )

    @classmethod
    def delete_one(
        cls,
        key: KeyProtocol | tuple | str,
    ) -> None:
        """Delete record for the specified key in object, tuple or string format (no error if not found)."""
        return active(DataSource).delete_one(key)

    @classmethod
    def delete_many(
        cls,
        keys: Sequence[KeyProtocol | tuple | str],
    ) -> None:
        """Delete records for the specified keys in object, tuple or string format (no error if not found)."""
        return active(DataSource).delete_many(keys)

    @classmethod
    def drop_test_db(cls) -> None:
        """
        Drop a database as part of a unit test.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - The method is invoked from a unit test based on ProcessContext.is_testing()
        - db_id starts with db_test_prefix specified in settings.yaml (the default prefix is 'test_')
        """
        active(DataSource).drop_test_db()

    @classmethod
    def drop_temp_db(cls, *, user_approval: bool) -> None:
        """
        Drop a temporary database with explicit user approval.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - user_approval is true
        - db_id starts with db_temp_prefix specified in settings.yaml (the default prefix is 'temp_')
        """
        active(DataSource).drop_temp_db(user_approval=user_approval)

    @classmethod
    def _pre_save_check(cls, record: RecordProtocol) -> None:
        if record is None:
            # Confirm argument is not None
            raise RuntimeError("Record passed to DB save method is None.")
        elif not is_record(record):
            # Confirm the argument is a record
            raise RuntimeError(f"Attempting to an object of {type(record).__name__} which is not a record.")
        elif not record.is_frozen():
            raise RuntimeError(
                f"Build method not invoked before saving for an record of type\n"
                f"{TypeUtil.name(record)} with key {record.get_key()}\n"
            )
        else:
            # TODO: To prevent calling get_key more than once, pass to DB save method
            if not KeySerializers.DELIMITED.serialize(key := record.get_key()):
                # Error only if not a singleton
                if not is_singleton_key(key):
                    record_data_str = BootstrapSerializers.YAML.serialize(record)
                    raise RuntimeError(
                        f"Attempting to save a record with empty key, invoke build before saving.\n"
                        f"Values of other fields:\n{record_data_str}"
                    )
