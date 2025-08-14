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

from __future__ import annotations
from inflection import titleize
from pydantic import BaseModel
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_kind import TypeKind


class TypesResponseItem(BaseModel):
    """Single item of the list returned by the /schema/types route."""

    name: str
    """Class name (may be customized in settings)."""

    label: str | None
    """Type label displayed in the UI is humanized class name (may be customized in settings)."""

    kind: str | None = None
    """Flag to indicate type kind."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_types(cls) -> list[TypesResponseItem]:  # TODO(Roman): !!! Separate routes for types and tables
        """Implements /schema/types route."""

        # Get types stored in DB
        ds = active(DataSource)
        record_type_names = ds.get_record_type_names()

        # Add types to result
        types_result = [
            TypesResponseItem(
                name=record_type_name,
                label=titleize(record_type_name),  # TODO: Make label different from name or remove
            )
            for record_type_name in record_type_names
        ]

        # Add tables to result
        tables_result = [
            TypesResponseItem(name=table, label=table, kind="Table")  # TODO: Make label different from name or remove
            for table in ds.get_tables()
        ]

        # Check name collisions between types and tables
        cls._check_name_collisions(types_result, tables_result)

        return tables_result + types_result

    @classmethod
    def _check_name_collisions(cls, types: list[TypesResponseItem], tables: list[TypesResponseItem]) -> None:
        """Check name collisions between types and tables."""
        collisions = set([x.name for x in types]) & set([x.name for x in tables])
        if collisions:
            raise RuntimeError(
                f"Name collision detected. The following names are used in both 'types' and 'tables': {', '.join(collisions)}"
            )
