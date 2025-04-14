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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
from cl.runtime.schema.type_kind import TypeKind


class TypesResponseItem(BaseModel):
    """Single item of the list returned by the /schema/types route."""

    name: str
    """Class name (may be customized in settings)."""

    label: str | None
    """Type label displayed in the UI is humanized class name (may be customized in settings)."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_types(cls) -> list[TypesResponseItem]:
        """Implements /schema/types route."""

        # Get cached classes (does not rebuild cache)
        record_types = TypeInfoCache.get_classes(type_kinds=(TypeKind.RECORD,))

        result = [
            TypesResponseItem(
                name=TypeUtil.name(record_type),
                label=titleize(TypeUtil.name(record_type)),
            )
            for record_type in record_types
        ]
        return result
