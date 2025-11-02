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

import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Sequence
from typing import cast
from memoization import cached
from cl.runtime.db.db import Db
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.db.save_policy import SavePolicy
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.file.file_util import FileUtil
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.data_mixin import TDataDict
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.key_mixin import TKey
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_mixin import TRecord
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.db_settings import DbSettings

_KEY_SERIALIZER = KeySerializers.DELIMITED
_DATA_SERIALIZER = DataSerializers.FOR_SQLITE

_connection_dict: dict[str, sqlite3.Connection] = {}
"""Dict of Connection instances with db_id key stored outside the class to avoid serialization."""

# Regex for a safe SQLite table name (letters, digits, underscores, start with letter or underscore)
_TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Regex for a safe SQLite column name (letters, digits, underscores, start with letter or underscore)
_COLUMN_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(slots=True, kw_only=True)
class SqliteDb(Db):

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

        if not keys:
            return []

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=key_type)

        if not self._table_exists(table_name=table_name):
            return tuple()

        serialized_keys = [_KEY_SERIALIZER.serialize(key) for key in keys]

        # Build SQL query to select records by keys
        placeholders = ",".join("?" for _ in serialized_keys)
        values = [tenant, *serialized_keys]
        select_sql = (
            f'SELECT * FROM {self._quote_identifier(table_name)} WHERE "_tenant" = ? AND "_key" IN ({placeholders})'
        )

        if sort_order is not None:
            # Add order by '_key' condition
            select_sql = self._add_order(select_sql, sort_field="_key", sort_order=sort_order)

        # Execute SQL query
        conn = self._get_connection()
        cursor = conn.execute(select_sql, values)

        # Deserialize records and return
        return [
            _DATA_SERIALIZER.deserialize({k: row[k] for k in row.keys() if row[k] is not None})
            for row in cursor.fetchall()
        ]

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

        if project_to is not None:
            raise RuntimeError(f"{typename(type(self))} does not currently support 'project_to' option.")

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=key_type)

        if not self._table_exists(table_name=table_name):
            return tuple()

        select_sql, values = f'SELECT * FROM {self._quote_identifier(table_name)} WHERE "_tenant" = ?', [tenant]

        if restrict_to is not None:
            # Add filter condition on type
            subtype_names = TypeInfo.get_child_and_self_type_names(restrict_to, type_kind=TypeKind.RECORD)
            placeholders = ",".join("?" for _ in subtype_names)

            select_sql += f' AND "_type" IN ({placeholders})'
            values += subtype_names

        # Add order by '_key' condition
        select_sql = self._add_order(select_sql, sort_field="_key", sort_order=sort_order)

        # Add 'limit' and 'skip' conditions
        select_sql, add_params = self._add_limit_and_skip(select_sql, limit=limit, skip=skip)
        values.extend(add_params)

        # Execute SQL query
        conn = self._get_connection()
        cursor = conn.execute(select_sql, values)

        # Deserialize records
        result = []
        for row in cursor.fetchall():
            # Convert sqlite3.Row to dict
            serialized_record = {k: row[k] for k in row.keys() if row[k] is not None}
            del serialized_record["_key"]

            # Create a record from the serialized data
            record = _DATA_SERIALIZER.deserialize(serialized_record)

            result.append(record)

        return tuple(result)

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

        if project_to is not None:
            raise RuntimeError(f"{typename(type(self))} does not currently support 'project_to' option.")

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=query.get_target_type().get_key_type())

        if not self._table_exists(table_name=table_name):
            return tuple()

        # Serialize the query
        query_dict = BootstrapSerializers.FOR_SQLITE_QUERY.serialize(query)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query.get_target_type()
        elif not issubclass(restrict_to, (query_target_type := query.get_target_type())):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {typename(type(self))}.load_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Build SQL query to select records in table by conditions
        where, values = self._convert_query_dict_to_sql_syntax(query_dict, tenant)

        if restrict_to is not None:
            # Add filter condition on type
            subtype_names = TypeInfo.get_child_and_self_type_names(restrict_to, type_kind=TypeKind.RECORD)
            placeholders = ",".join("?" for _ in subtype_names)

            if where:
                where += " AND "

            where += f'"_type" IN ({placeholders})'
            values += subtype_names

        select_sql = f'SELECT * FROM {self._quote_identifier(table_name)} WHERE "_tenant" = ?'

        if where:
            select_sql += f" AND {where}"

        # Add order by '_key' condition
        select_sql = self._add_order(select_sql, sort_field="_key", sort_order=sort_order)

        # Add 'limit' and 'skip' conditions
        select_sql, add_params = self._add_limit_and_skip(select_sql, limit=limit, skip=skip)
        values.extend(add_params)

        # Execute SQL query
        conn = self._get_connection()
        cursor = conn.execute(select_sql, values)

        # Set cast_to to restrict_to if not specified
        if cast_to is None:
            cast_to = restrict_to

        # Deserialize records
        result = []
        for row in cursor.fetchall():
            # Convert sqlite3.Row to dict
            serialized_record = {k: row[k] for k in row.keys() if row[k] is not None}
            del serialized_record["_key"]

            # Create a record from the serialized data
            record = _DATA_SERIALIZER.deserialize(serialized_record)

            # Apply cast (error if not a subtype)
            record = CastUtil.cast(cast_to, record)
            result.append(record)

        return tuple(result)

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
        table_name = self._get_validated_table_name(key_type=query.get_target_type().get_key_type())

        if not self._table_exists(table_name=table_name):
            return 0

        # TODO (Roman): Use a specialized serializer for SQL query.
        # Serialize the query
        query_dict = BootstrapSerializers.FOR_SQLITE_QUERY.serialize(query)

        # Validate restrict_to or use the query target type if not specified
        if restrict_to is None:
            # Default to the query target type
            restrict_to = query.get_target_type()
        elif not issubclass(restrict_to, (query_target_type := query.get_target_type())):
            # Ensure restrict_to is a subclass of the query target type
            raise RuntimeError(
                f"In {typename(type(self))}.load_by_query, restrict_to={typename(restrict_to)} is not a subclass\n"
                f"of the target type {typename(query_target_type)} for {typename(query)}."
            )

        # Build SQL query to count records in table by conditions
        where, values = self._convert_query_dict_to_sql_syntax(query_dict, tenant)

        if restrict_to is not None:
            # Add filter condition on type
            subtype_names = TypeInfo.get_child_and_self_type_names(restrict_to, type_kind=TypeKind.RECORD)
            placeholders = ",".join("?" for _ in subtype_names)

            if where:
                where += " AND "

            where += f'"_type" IN ({placeholders})'
            values += subtype_names

        select_sql = f'SELECT COUNT(*) FROM {self._quote_identifier(table_name)} WHERE "_tenant" = ?'

        if where:
            select_sql += f" AND {where}"

        # Execute SQL query
        conn = self._get_connection()
        cursor = conn.execute(select_sql, values)

        count = cursor.fetchone()[0]
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

        if not records:
            return

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=key_type)

        # Create table if not exists using key_type as source for table schema
        self._create_table(key_type=key_type)

        serialized_records = []
        for record in records:
            serialized_record = _DATA_SERIALIZER.serialize(record)
            serialized_record["_key"] = _KEY_SERIALIZER.serialize(record.get_key())
            serialized_record["_tenant"] = tenant
            serialized_records.append(serialized_record)

        # Dynamically determine all relevant columns to use for query
        columns_for_query = sorted(set(k for data in serialized_records for k in data.keys()))

        # Build SQL query to insert records
        quoted_cols = [self._quote_identifier(self._get_validated_column_name(c)) for c in columns_for_query]
        placeholders = ", ".join("?" for _ in quoted_cols)

        if save_policy == SavePolicy.INSERT:
            # Insert the record, error if already exists
            sql_command = "INSERT"
        elif save_policy == SavePolicy.REPLACE:
            # Add record to cache, overwriting an existing record if present
            sql_command = "INSERT OR REPLACE"
        else:
            ErrorUtil.enum_value_error(save_policy, SavePolicy)

        insert_sql = f"{sql_command} INTO {self._quote_identifier(table_name)} ({', '.join(quoted_cols)}) VALUES ({placeholders})"

        # Build values for SQL query
        values_for_query = [tuple(data.get(col) for col in columns_for_query) for data in serialized_records]

        # Execute SQL query
        conn = self._get_connection()
        conn.executemany(insert_sql, values_for_query)
        conn.commit()

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

        if not keys:
            return

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=key_type)

        if not self._table_exists(table_name=table_name):
            return

        serialized_keys = [_KEY_SERIALIZER.serialize(key) for key in keys]

        # Build SQL query to delete records by keys
        placeholders = ",".join("?" for _ in serialized_keys)
        values = [tenant, *serialized_keys]
        select_sql = (
            f'DELETE FROM {self._quote_identifier(table_name)} WHERE "_tenant" = ? AND "_key" IN ({placeholders})'
        )

        # Execute SQL query
        conn = self._get_connection()
        conn.execute(select_sql, values)

    def delete_by_query(
        self,
        query: QueryMixin,
        *,
        dataset: str,
        tenant: str,
        restrict_to: type | None = None,
    ) -> None:
        raise NotImplementedError()  # TODO: !!!! Implement

    def drop_test_db(self) -> None:
        # Check preconditions
        self.check_drop_test_db_preconditions()

        # Drop the entire database without possibility of recovery.
        # This relies on the preconditions check above to prevent unintended use
        self._drop_db()

    def drop_temp_db(self, *, user_approval: bool) -> None:
        # Check preconditions
        self.check_drop_temp_db_preconditions(user_approval=user_approval)

        # Drop the entire database without possibility of recovery.
        # This relies on the preconditions check above to prevent unintended use
        self._drop_db()

    def close_connection(self) -> None:
        if (connection := _connection_dict.get(self.db_id, None)) is not None:
            # Close connection
            connection.close()

            # Remove from dictionary so connection can be reopened on next access
            del _connection_dict[self.db_id]

    def _get_db_file_path(self) -> str:
        """Get database file path from db_id, applying the appropriate formatting conventions."""

        # Check that db_id is a valid filename
        FileUtil.guard_valid_filename(self.db_id)

        # Get dir for database
        db_dir = DbSettings.get_db_dir()

        result = os.path.join(db_dir, f"{self.db_id}.sqlite")
        return result

    def _get_connection(self) -> sqlite3.Connection:
        """Get sqlite3 connection object."""

        if (conn := _connection_dict.get(self.db_id, None)) is None:
            db_file_path = self._get_db_file_path()

            # Ensure the parent directory exists
            os.makedirs(os.path.dirname(db_file_path), exist_ok=True)

            # Open a connection to the SQLite database at the given path.
            # If the file does not exist, SQLite will create it (but not directory)
            conn = sqlite3.connect(db_file_path, check_same_thread=False)

            # Enable Write-Ahead Logging (WAL) mode.
            # This improves concurrent read/write performance and reduces locking issues.
            conn.execute("PRAGMA journal_mode=WAL")

            # Set the synchronous mode to 'NORMAL' to balance performance and durability.
            # It's faster than FULL, and still safe for most use cases.
            conn.execute("PRAGMA synchronous=NORMAL")

            # Set the row factory so that rows fetched from queries will be returned
            # as sqlite3.Row objects, which act like dictionaries (column access by name).
            conn.row_factory = sqlite3.Row

            _connection_dict[self.db_id] = conn

        return conn

    def _create_table(self, *, key_type: type[KeyMixin]) -> None:
        """Create a table if not exists with a structure corresponding to the key_type hierarchy."""

        # Get table name from key type and check it has an acceptable format
        table_name = self._get_validated_table_name(key_type=key_type)

        # List of columns that are present in the table by default
        column_defs = ["_key", "_type", "_tenant"]

        # Validate and quote data type columns
        column_defs.extend(
            (
                self._quote_identifier(self._get_validated_column_name(column_name))
                for column_name in self._extract_columns_for_key_type(key_type)
            )
        )

        sql = (
            f"CREATE TABLE IF NOT EXISTS {self._quote_identifier(table_name)} "
            + f'({", ".join(column_defs)}, PRIMARY KEY (_key, _tenant));'
        )

        conn = self._get_connection()
        conn.execute(sql)
        conn.commit()

    def _table_exists(self, *, table_name: str) -> bool:
        """Check if specified table exists in DB."""

        check_sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        conn = self._get_connection()
        return conn.execute(check_sql, (table_name,)).fetchone()

    def _drop_db(self):
        """Delete db file."""
        # Close connection
        self.close_connection()

        # Drop the entire database file without possibility of recovery.
        # This relies on the preconditions check above to prevent unintended use.
        db_file_path = self._get_db_file_path()
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    @classmethod
    def _add_limit_and_skip(
        cls, select_sql: str, *, limit: int | None = None, skip: int | None = None
    ) -> tuple[str, list]:
        """Add 'limit' and 'skip' conditions to sql query."""

        add_params = []

        if limit is not None:
            select_sql += " LIMIT ?"
            add_params.append(limit)
            if skip is not None:
                select_sql += " OFFSET ?"
                add_params.append(skip)
        elif skip is not None:
            # Use LIMIT -1 to enable OFFSET
            select_sql += " LIMIT -1 OFFSET ?"
            add_params.append(skip)

        return select_sql, add_params

    @classmethod
    def _add_order(cls, select_sql: str, sort_field: str, sort_order: SortOrder) -> str:
        """Add 'order' conditions to sql query."""
        if sort_order == SortOrder.UNORDERED:
            return select_sql  # no sort applied
        elif sort_order == SortOrder.ASC:
            return select_sql + f' ORDER BY "{sort_field}" ASC'
        elif sort_order == SortOrder.DESC:
            return select_sql + f' ORDER BY "{sort_field}" DESC'
        elif sort_order == SortOrder.INPUT:
            # Not implemented. Return unchanged query by default.
            return select_sql
        else:
            raise ValueError(f"Unsupported SortOrder: {sort_order}")

    @classmethod
    def _extract_columns_for_key_type(cls, key_type: type[TKey]) -> list[str]:
        """Get columns according to the fields of all descendant classes from the specified key."""

        # Get child type names for key_type
        child_record_type_names = TypeInfo.get_child_and_self_type_names(key_type, type_kind=TypeKind.RECORD)
        result_columns = []

        # Iterate through child types and add unique columns.
        # Since child types are sorted by depth in the hierarchy, the base fields will be at the beginning.
        for child in child_record_type_names:
            # Add unique columns from child fields
            child_type = cast(type[DataMixin], TypeInfo.from_type_name(child))
            add_columns = set(child_type.get_field_names()) - set(result_columns)
            result_columns.extend(add_columns)

        return result_columns

    @classmethod
    def _extract_columns_for_data(cls, data: list[TDataDict]) -> list[str]:
        """Returns a list of columns that are in at least one data item."""

        if not data:
            return []

        result_columns_set = set(k for data_item in data for k in data_item.keys())
        return sorted(result_columns_set)

    @classmethod
    @cached
    def _get_validated_table_name(cls, *, key_type: type[KeyMixin]):
        """Get table name from key type and check that it has an acceptable format or length, error otherwise."""
        table_name = typename(key_type).removesuffix("Key")
        if _TABLE_NAME_RE.fullmatch(table_name) is None:
            raise RuntimeError(f"Table name '{table_name}' is not valid for {typename(cls)}")
        return table_name

    @classmethod
    @cached
    def _get_validated_column_name(cls, column_name: str) -> str:
        """Return column name if it has an acceptable format or length, error otherwise."""
        if _COLUMN_NAME_RE.fullmatch(column_name) is None:
            raise RuntimeError(f"Column name '{column_name}' is not valid for {typename(cls)}")
        return column_name

    @classmethod
    @cached
    def _quote_identifier(cls, identifier: str) -> str:
        """Quote SQLite identifier."""

        # Quote identifier with double quotes, escape embedded quotes if any
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    @classmethod
    def _convert_query_dict_to_sql_syntax(cls, query_dict: dict, tenant: str) -> tuple[str, list]:
        """
        Create query dict to SQL syntax 'WHERE' clause.
        Returns a tuple of two values, where the first is an SQL string with placeholders,
        and the second is the values for the placeholders.
        """

        clauses = []
        values = [tenant]

        for key, value in query_dict.items():
            if isinstance(value, dict):
                # Only support 1 operator per field
                if len(value) != 1:
                    raise RuntimeError(f"Multiple operators not supported per field: {value}")

                op, v = next(iter(value.items()))

                if op == "op_in":
                    if not isinstance(v, (list, tuple)) or not v:
                        raise RuntimeError(f"'op_in' must have non-empty list/tuple value: {v}")
                    placeholders = ", ".join("?" for _ in v)
                    clauses.append(f"{cls._quote_identifier(key)} IN ({placeholders})")
                    values.extend(v)
                elif op == "op_nin":
                    if not isinstance(v, (list, tuple)) or not v:
                        raise RuntimeError(f"'op_in' must have non-empty list/tuple value: {v}")
                    placeholders = ", ".join("?" for _ in v)
                    clauses.append(f"{cls._quote_identifier(key)} NOT IN ({placeholders})")
                    values.extend(v)
                elif op == "op_gt":
                    clauses.append(f"{cls._quote_identifier(key)} > ?")
                    values.append(v)
                elif op == "op_gte":
                    clauses.append(f"{cls._quote_identifier(key)} >= ?")
                    values.append(v)
                elif op == "op_lt":
                    clauses.append(f"{cls._quote_identifier(key)} < ?")
                    values.append(v)
                elif op == "op_lte":
                    clauses.append(f"{cls._quote_identifier(key)} <= ?")
                    values.append(v)
                elif op == "op_exists":
                    if v is True:
                        clauses.append(f"{key} IS NOT NULL")
                    elif v is False:
                        clauses.append(f"{key} IS NULL")
                    else:
                        raise ValueError(f"op_exists must be True or False, got: {v}")
                else:
                    raise RuntimeError(f"Unsupported operator: {op}")
            else:
                # Simple equality
                clauses.append(f"{cls._quote_identifier(key)} = ?")
                values.append(value)

        where_clause = " AND ".join(clauses)
        return where_clause, values
