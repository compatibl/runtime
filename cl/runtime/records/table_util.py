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

from typing import Final
from typing import Iterable
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import TKey
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.table import Table
from cl.runtime.records.type_util import TypeUtil

_TABLE_PREFIX: Final[str] = "_table_"
"""Prefix for a type name in schema to mark tables."""


class TableUtil:
    """Utilities for working with tables."""

    @classmethod
    def get_table(cls, record_or_key: TRecord | TKey) -> str:
        """Get table name from type, validate format and remove Key suffix if present."""

        # Check that the argument is not empty
        if record_or_key is None:
            raise RuntimeError("The argument of TableUtil.get_table is None or empty.")

        # Get table name from record or key
        table = record_or_key.get_table()

        # Ensure table is not empty
        if not table:
            raise RuntimeError(
                f"The result of get_table for {TypeUtil.name(record_or_key)} is None or empty.\n"
                f"Ensure all fields of the argument that determine the table are set."
            )

        # Validate PascalCase format
        if not CaseUtil.is_pascal_case(table):
            raise RuntimeError(
                f"Table name {table} for key type {TypeUtil.name(record_or_key)} is not in PascalCase format\n"
                f"or does not follow the custom rule for separators in front of digits."
            )

        # Remove Key suffix if present
        # TODO: Restore which will also test that this method is used consistently everywhere
        # if table.endswith("Key"):
        #    table = table.removesuffix("Key")

        return table

    @classmethod
    def get_tables_in_records(cls, records: Iterable[TRecord]) -> list[Table]:
        """Get a list of Table objects of tables needed to place records."""

        # Add table for 'Table' class by default
        tables_in_records = {cls.get_table(Table()): Table.get_key_type()}

        for record in records:
            table = cls.get_table(record)
            # TODO (Roman): Ensure that different key type records dont have the same table
            if table not in tables_in_records:
                tables_in_records[table] = record.get_key().get_key_type()

        return [
            Table(table_id=table_id, key_type=TypeUtil.name(key_type)).build()
            for table_id, key_type in tables_in_records.items()
        ]

    @classmethod
    def get_tables(cls, for_key_type: str | None = None) -> Iterable[Table]:
        """Get iterable of Table records for key type name. If 'for_key_type' is None - return all tables."""

        # TODO: Refactor to avoid inline import
        from cl.runtime.contexts.db_context import DbContext

        all_tables = DbContext.load_all(Table, tables=[Table().get_table()])

        if for_key_type is not None:
            return [x for x in all_tables if x.key_type == for_key_type]

        return all_tables

    @classmethod
    def is_table(cls, table_or_type: str) -> bool:
        """Check if 'table_or_type' is a table."""

        return table_or_type.startswith(_TABLE_PREFIX)

    @classmethod
    def get_table_schema_type(cls, table: str) -> str:
        """Find table key type by table name and return first child of key as a schema type."""

        from cl.runtime import TypeInfoCache

        table_id = cls.remove_table_prefix(table)
        all_tables = cls.get_tables()
        table = next((table for table in all_tables if table.table_id == table_id), None)

        if table is None:
            raise RuntimeError(f"Unknown table: {table_id}.")

        key_type = TypeInfoCache.get_class_from_type_name(table.key_type)
        key_descendants = TypeInfoCache.get_child_names(key_type)

        # Determine schema type for table
        # Consider first child of key type to be schema type for table
        # TODO (Roman): Support derived types to be schema type for table
        if len(key_descendants) > 1:
            first_child = next(
                (child_class for child_class in key_descendants if child_class != TypeUtil.name(key_type)), None
            )
            if first_child is not None:
                return first_child

        # If child not found - return key type as schema type
        return TypeUtil.name(key_type)

    @classmethod
    def add_table_prefix(cls, table: str) -> str:
        """Add table prefix to table name."""

        if table.startswith(_TABLE_PREFIX):
            return table
        else:
            return _TABLE_PREFIX + table

    @classmethod
    def remove_table_prefix(cls, table: str) -> str:
        """Remove table prefix from table name."""

        if table.startswith(_TABLE_PREFIX):
            return table[len(_TABLE_PREFIX) :]
        else:
            return table
