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
import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Iterable
from typing import Sequence
from typing import Tuple
from more_itertools import consume
from cl.runtime import KeyUtil
from cl.runtime import RecordMixin
from cl.runtime.db.db import Db
from cl.runtime.db.sql.sqlite_schema_manager import SqliteSchemaManager
from cl.runtime.file.file_util import FileUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.table_util import TableUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.db_settings import DbSettings

_KEY_SERIALIZER = KeySerializers.FOR_SQLITE
_SERIALIZER = DataSerializers.FOR_SQLITE

_connection_dict: Dict[str, sqlite3.Connection] = {}
"""Dict of Connection instances with db_id key stored outside the class to avoid serialization."""

_schema_manager_dict: Dict[str, SqliteSchemaManager] = {}
"""Dict of SqliteSchemaManager instances with db_id key key stored outside the class to avoid serialization."""


def dict_factory(cursor, row):
    """sqlite3 row factory to return result as dictionary."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


@dataclass(slots=True, kw_only=True)
class SqliteDb(Db):
    """Sqlite database without dataset and mile wide table for inheritance."""

    def batch_size(self) -> int:
        pass

    @classmethod
    def _add_where_keys_in_clause(
        cls,
        sql_statement: str,
        key_fields: Tuple[str, ...],
        columns_mapping: Dict[str, str],
        keys_len: int,
    ) -> str:
        """
        Add "WHERE (key_field1, ...) IN ((value1_for_field1, ...), (value2_for_field1, ...), ...)" clause to
        sql_statement.
        """

        # if key fields isn't empty add WHERE clause
        if key_fields:
            value_places = ", ".join([f'({", ".join(["?"] * len(key_fields))})' for _ in range(keys_len)])
            key_column_str = ", ".join([f'"{columns_mapping[key]}"' for key in key_fields])

            # add WHERE clause to sql_statement
            sql_statement += f" WHERE ({key_column_str}) IN ({value_places})"

        return sql_statement

    @classmethod
    def _serialize_keys_to_flat_tuple(cls, keys: Iterable[KeyProtocol]) -> Tuple[Any, ...]:
        """
        Sequentially serialize key fields for each key in keys into a flat tuple of values.
        Expected all keys are of the same type for which key fields are specified.
        """
        key_tuples = tuple(_KEY_SERIALIZER.serialize(key) for key in keys)
        flattened_tuple = tuple(item for group in key_tuples for item in group)
        return flattened_tuple  # TODO(Roman): Review why it should be flattened

    def load_many_unsorted(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> Sequence[RecordMixin]:

        # Return an empty list if the table does not exist for the derived type
        schema_manager = self._get_schema_manager()
        existing_tables = schema_manager.existing_tables()
        if table not in existing_tables:
            return []

        # Ensure all keys within the table have the same type and get that type, error otherwise
        key_type = KeyUtil.get_key_type(table=table, records_or_keys=keys)

        key_fields = schema_manager.get_primary_keys(key_type)
        columns_mapping = schema_manager.get_columns_mapping(key_type)

        # if keys_group don't support "in" or "len" operator convert it to tuple
        sql_statement = f'SELECT * FROM "{table}"'
        sql_statement = self._add_where_keys_in_clause(sql_statement, key_fields, columns_mapping, len(keys))
        sql_statement += ";"

        # TODO: Check the logic for multiple keys when the tuple is flattened
        serialized_keys = [_KEY_SERIALIZER.serialize(key) for key in keys]
        flattened_tuple = tuple(item for group in serialized_keys for item in group)

        cursor = self._get_connection().cursor()
        try:
            cursor.execute(sql_statement, flattened_tuple)
        except Exception as e:
            raise RuntimeError(str(keys))

        reversed_columns_mapping = {v: k for k, v in columns_mapping.items()}

        # TODO (Roman): investigate performance impact from this ordering approach
        # bulk load from db returns records in any order so we need to check all records in group before return
        # collect db result to dictionary to return it according to input keys order
        result = []
        for data in cursor.fetchall():
            # TODO (Roman): select only needed columns on db side.
            data = {reversed_columns_mapping[k]: v for k, v in data.items() if v is not None}
            deserialized_data = _SERIALIZER.deserialize(data)

            # TODO (Roman): make key hashable and remove conversion of key to str
            result.append(deserialized_data)
        return result

    def load_all(
        self,
        table: str,
        record_type: type[TRecord],
        *,
        dataset: str | None = None,
    ) -> Iterable[TRecord | None] | None:
        schema_manager = self._get_schema_manager()

        # if table doesn't exist return empty list
        if table not in schema_manager.existing_tables():
            return list()

        # using primary keys (which are fields from key type) to sort the selection
        pk_cols = [f'"{table}.{col}"' for col in schema_manager.get_primary_keys(record_type)]
        sort_columns = ", ".join(pk_cols)

        # get subtypes for record_type and use them in match condition
        subtype_names = TypeInfoCache.get_child_names(record_type)
        value_placeholders = ", ".join(["?"] * len(subtype_names))
        sql_statement = f'SELECT * FROM "{table}" WHERE _type in ({value_placeholders})'

        if sort_columns:
            sql_statement += f" ORDER BY {sort_columns};"
        else:
            sql_statement += ";"

        reversed_columns_mapping = {
            v: k for k, v in schema_manager.get_columns_mapping(record_type.get_key_type()).items()
        }

        cursor = self._get_connection().cursor()
        cursor.execute(sql_statement, subtype_names)

        # TODO: Implement sort in query and restore yield to support large collections
        result = []
        for data in cursor.fetchall():
            # TODO (Roman): Select only needed columns on db side.
            data = {reversed_columns_mapping[k]: v for k, v in data.items() if v is not None}
            yield _SERIALIZER.deserialize(data)

    def load_where(
        self,
        query: QueryMixin,
        *,
        dataset: str | None = None,
        cast_to: type | None = None,
        limit: int | None = None,
        skip: int | None = None,
    ) -> Sequence[RecordMixin]:
        raise NotImplementedError()

    def save_many(
        self,
        records: Iterable[RecordProtocol],
        *,
        dataset: str | None = None,
    ) -> None:

        # Add Table objects to records to save
        # TODO (Roman): Improve performance
        tables = TableUtil.get_tables_in_records(records)
        records_to_save = itertools.chain(records, tables)

        schema_manager = self._get_schema_manager()

        # Group keys by table
        records_grouped_by_table = defaultdict(list)
        consume(records_grouped_by_table[TableUtil.get_table(record)].append(record) for record in records_to_save)

        # Iterate over tables
        for table, table_records in records_grouped_by_table.items():

            # Ensure all keys within the table have the same type and get that type, error otherwise
            key_type = KeyUtil.get_key_type(table=table, records_or_keys=table_records)

            # Serialize records
            serialized_records = [_SERIALIZER.serialize(rec) for rec in table_records]

            # Get maximum set of fields from records
            all_fields = list({k for rec in serialized_records for k in rec.keys()})

            # Fill sql_values with ordered values from serialized records
            # if field isn't in some records - fill with None
            sql_values = tuple(
                serialized_record[k] if k in serialized_record else None
                for serialized_record in serialized_records
                for k in all_fields
            )

            columns_mapping = schema_manager.get_columns_mapping(key_type)
            quoted_columns = [f'"{columns_mapping[field]}"' for field in all_fields]
            columns_str = ", ".join(quoted_columns)

            primary_keys = [columns_mapping[primary_key] for primary_key in schema_manager.get_primary_keys(key_type)]

            schema_manager.create_table(table, columns_mapping.values(), if_not_exists=True, primary_keys=primary_keys)

            value_placeholders = ", ".join([f"({', '.join(['?']*len(all_fields))})" for _ in range(len(table_records))])
            sql_statement = f'REPLACE INTO "{table}" ({columns_str}) VALUES {value_placeholders};'

            if not primary_keys:
                # TODO (Roman): this is a workaround for handling singleton records.
                #  Since they don't have primary keys, we can't automatically replace existing records.
                #  So this code just deletes the existing records before saving.
                #  As a possible solution, we can introduce some mandatory primary key that isn't based on the
                #  key fields.
                self.delete_many(table, (rec.get_key() for rec in table_records))

            connection = self._get_connection()
            cursor = connection.cursor()
            try:
                cursor.execute(sql_statement, sql_values)
            except Exception as e:
                raise RuntimeError(
                    f"An exception occurred during SQL command execution for save_many: {e}\n"
                    f"SQL values: {sql_values}\n"
                ) from e

            connection.commit()

    def delete_many(
        self,
        table: str,
        keys: Sequence[KeyMixin],
        *,
        dataset: str | None = None,
    ) -> None:
        schema_manager = self._get_schema_manager()

        # TODO (Roman): improve grouping
        grouped_keys = defaultdict(list)
        for key in keys:
            grouped_keys[key.get_key_type()].append(key)

        for key_type, keys_group in grouped_keys.items():

            existing_tables = schema_manager.existing_tables()
            if table not in existing_tables:
                continue

            key_fields = schema_manager.get_primary_keys(key_type)
            columns_mapping = schema_manager.get_columns_mapping(key_type)

            # if keys_group don't support "in" or "len" operator convert it to tuple
            if not hasattr(keys_group, "__contains__") or not hasattr(keys_group, "__len__"):
                keys_group = tuple(keys_group)

            # construct sql_statement with placeholders for values
            sql_statement = f'DELETE FROM "{table}"'
            sql_statement = self._add_where_keys_in_clause(sql_statement, key_fields, columns_mapping, len(keys_group))
            sql_statement += ";"

            # serialize keys to tuple
            query_values = self._serialize_keys_to_flat_tuple(keys_group)

            # perform delete query
            connection = self._get_connection()
            cursor = connection.cursor()
            cursor.execute(sql_statement, query_values)
            connection.commit()

    def drop_temp_db(self) -> None:
        # Error if db_id does not start from the db_temp_prefix specified in settings.yaml (defaults to 'temp_')
        self.error_if_not_temp_db()

        # Close connection
        self.close_connection()

        # Check that filename also matches temp_db_prefix. It should normally match db_id
        # we already checked, but given the critical importance of this check will check db_filename
        # as well in case this approach changes later.
        db_file_path = self._get_db_file()

        # Delete database file if exists, all checks gave been performed
        if os.path.exists(db_file_path):
            os.remove(db_file_path)

    def close_connection(self) -> None:
        if (connection := _connection_dict.get(self.db_id, None)) is not None:
            # Close connection
            connection.close()
            # Remove from dictionary so connection can be reopened on next access
            del _connection_dict[self.db_id]
            del _schema_manager_dict[self.db_id]

    def _get_connection(self) -> sqlite3.Connection:
        """Get PyMongo database object."""
        if (connection := _connection_dict.get(self.db_id, None)) is None:
            # TODO: Implement dispose logic
            db_file = self._get_db_file()
            connection = sqlite3.connect(db_file, check_same_thread=False)
            connection.row_factory = dict_factory
            _connection_dict[self.db_id] = connection
        return connection

    def _get_schema_manager(self) -> SqliteSchemaManager:
        """Get PyMongo database object."""
        if (result := _schema_manager_dict.get(self.db_id, None)) is None:
            # TODO: Implement dispose logic
            connection = self._get_connection()
            result = SqliteSchemaManager(sqlite_connection=connection)
            _schema_manager_dict[self.db_id] = result
        return result

    def _get_db_file(self) -> str:
        """Get database file path from db_id, applying the appropriate formatting conventions."""

        # Check that db_id is a valid filename
        filename = self.db_id
        FileUtil.check_valid_filename(filename)

        # Get dir for database
        db_dir = DbSettings.get_db_dir()
        os.makedirs(db_dir, exist_ok=True)

        result = os.path.join(db_dir, f"{filename}.sqlite")
        return result

    def is_empty(self) -> bool:
        """Return True if the database has no tables or all tables are empty."""
        connection = self._get_connection()
        cursor = connection.cursor()

        # Check if there are any tables in the SQLite database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # If no tables are present, the database is empty
        if not tables:
            return True

        # Check if all tables are empty
        for table_name in tables:
            table_name = table_name["name"]
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
            count = cursor.fetchone()["COUNT(*)"]

            # If any table has data, the database is not empty
            if count > 0:
                return False

        return True
