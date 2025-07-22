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
from typing import Sequence, Iterable

from cl.runtime import Db, RecordMixin
from cl.runtime.file.file_util import FileUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import RecordProtocol, TRecord, TKey
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.db_settings import DbSettings

_KEY_SERIALIZER = KeySerializers.FOR_SQLITE
_DATA_SERIALIZER = DataSerializers.FOR_SQLITE

_connection_dict: dict[str, sqlite3.Connection] = {}
"""Dict of Connection instances with db_id key stored outside the class to avoid serialization."""

# Regex for a safe SQLite identifier (letters, digits, underscores, start with letter or underscore)
IDENTIFIER_REGEX = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


@dataclass(slots=True, kw_only=True)
class SqliteDbV2(Db):

    def load_table(self, table: str, *, dataset: str | None = None, cast_to: type[TRecord] | None = None,
                   filter_to: type[TRecord] | None = None, project_to: type[TRecord] | None = None,
                   limit: int | None = None, skip: int | None = None) -> tuple[TRecord]:
        pass

    def load_many_unsorted(self, table: str, keys: Sequence[KeyMixin], *, dataset: str | None = None) -> Sequence[
        RecordMixin]:
        pass

    def load_where(self, query: QueryMixin, *, dataset: str | None = None, cast_to: type[TRecord] | None = None,
                   filter_to: type[TRecord] | None = None, project_to: type[TRecord] | None = None,
                   limit: int | None = None, skip: int | None = None) -> tuple[TRecord]:
        pass

    def save_many(self, records: Iterable[RecordProtocol], *, dataset: str | None = None) -> None:
        pass

    def delete_many(self, table: str, keys: Sequence[KeyMixin], *, dataset: str | None = None) -> None:
        pass

    def count_where(self, query: QueryMixin, *, dataset: str | None = None, filter_to: type | None = None) -> int:
        pass

    def drop_test_db(self) -> None:
        pass

    def drop_temp_db(self, *, user_approval: bool) -> None:
        pass

    def close_connection(self) -> None:
        if (connection := _connection_dict.get(self.db_id, None)) is not None:
            # Close connection
            connection.close()

            # Remove from dictionary so connection can be reopened on next access
            del _connection_dict[self.db_id]

    def _get_connection(self) -> sqlite3.Connection:
        """Get sqlite3 connection object."""

        if (conn := _connection_dict.get(self.db_id, None)) is None:
            db_file_path = self._get_db_file_path(self.db_id)

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

    def _create_table(self, table: str, key_type: type[TKey]) -> None:
        """Create a table with a structure corresponding to the key_type hierarchy."""

        # Validate table name
        self._check_safe_identifier(table)

        # List of columns that are present in the table by default
        column_defs = ["_key PRIMARY KEY", "_type"]

        # Validate and quote data type columns
        column_defs.extend(
            (self._quote_identifier(x) for x in self._get_columns_for_key_type(key_type) if self._check_safe_identifier(x))
        )

        sql = f"CREATE TABLE IF NOT EXISTS {self._quote_identifier(table)} ({', '.join(column_defs)})"

        conn = self._get_connection()
        conn.execute(sql)
        conn.commit()

    def _get_columns_for_key_type(self, key_type: type[TKey]) -> list[str]:
        """Get columns according to the fields of all descendant classes from the specified key."""
        ...

    @classmethod
    def _check_safe_identifier(cls, identifier: str) -> bool:
        """Check whether the SQLite identifier does not contain prohibited characters."""

        is_safe = IDENTIFIER_REGEX.fullmatch(identifier) is not None

        if not is_safe:
            raise RuntimeError(f"Unsafe identifier: {identifier}")

        return is_safe

    @classmethod
    def _quote_identifier(cls, identifier: str) -> str:
        """Quote SQLite identifier."""

        # Quote identifier with double quotes, escape embedded quotes if any
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    @classmethod
    def _get_db_file_path(cls, db_id: str) -> str:
        """Get database file path from db_id, applying the appropriate formatting conventions."""

        # Check that db_id is a valid filename
        FileUtil.check_valid_filename(db_id)

        # Get dir for database
        db_dir = DbSettings.get_db_dir()

        result = os.path.join(db_dir, f"{db_id}.sqlite")
        return result