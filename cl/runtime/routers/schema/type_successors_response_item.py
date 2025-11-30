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
from cl.runtime.records.protocols import is_abstract_type
from cl.runtime.records.typename import typename
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind


class TypeSuccessorsResponseItem(BaseModel):
    """Single item of the list returned by the /schema/type-successors route."""

    name: str
    """Class name (may be customized in settings)."""

    label: str | None
    """Type label displayed in the UI is humanized class name (may be customized in settings)."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_type_successors(cls, request: TypeRequest) -> list[TypeSuccessorsResponseItem]:
        """Implements /schema/type-successors route."""

        # Getting child record type names
        base_record_type = TypeInfo.from_type_name(request.type_name)
        child_record_types = TypeInfo.get_child_and_self_types(base_record_type, type_kind=TypeKind.RECORD)
        result = [
            TypeSuccessorsResponseItem(name=typename(record_type), label=titleize(typename(record_type)))
            for record_type in child_record_types
            if not is_abstract_type(record_type)
        ]
        return result
