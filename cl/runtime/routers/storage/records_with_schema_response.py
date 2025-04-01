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

from typing import Type

from pydantic import BaseModel

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil


class RecordsWithSchemaResponse(BaseModel):
    """Class for records with schema response."""

    schema: dict
    """Schema dict."""

    data: list[dict]
    """List of records."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def _get_schema_dict(cls, type_: Type | None) -> dict[str, dict]:
        """Create schema dict for type. If 'type_' is None - return empty dict."""
        return TypeResponseUtil.get_type(TypeRequest(type_name=type_.__name__)) if type_ is not None else dict()
