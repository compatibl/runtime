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
from pydantic import BaseModel

from cl.runtime.contexts.data_context import DataContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.schema.type_request import TypeRequest


class TypeTablesResponseItem(BaseModel):
    """Single item of the list returned by the /schema/type-tables route."""

    name: str
    """Table name (may be customized in settings)."""

    label: str | None = None
    """Table label displayed in the UI is humanized class name (may be customized in settings)."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_type_tables(cls, request: TypeRequest) -> list[TypeTablesResponseItem]:
        """Implements /schema/type-tables route."""

        bound_type_name = request.type_name
        bindings = DataContext.get_bound_tables(record_type=bound_type_name)

        return [TypeTablesResponseItem(name=type_name) for type_name in bindings]
