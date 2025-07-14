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
    def get_tables(cls, for_key_type: str | None = None) -> Iterable[Table]:
        """Get iterable of Table records for key type name. If 'for_key_type' is None - return all tables."""

        # TODO: Refactor to avoid inline import
        from cl.runtime.contexts.db_context import DbContext

        all_tables = DbContext.load_type(Table, tables=[Table().get_table()])

        if for_key_type is not None:
            return [x for x in all_tables if x.key_type == for_key_type]

        return all_tables

    @classmethod
    def is_table(cls, table_or_type: str) -> bool:
        """Check if 'table_or_type' is a table."""

        return table_or_type.startswith(_TABLE_PREFIX)

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
