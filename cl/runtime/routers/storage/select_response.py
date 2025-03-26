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
from typing import Any
from typing import Dict
from typing import List
from pydantic import BaseModel
from pydantic import Field
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.records.class_info import ClassInfo
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.ui_dict_serializer import UiDictSerializer

ui_serializer = UiDictSerializer()
_UI_SERIALIZER = DataSerializers.FOR_UI


class SelectResponse(BaseModel):
    """Response data type for the /storage/select route."""

    schema_: Dict[str, Any] = Field(..., alias="schema")
    """Schema field of the response data type for the /storage/select route."""

    data: List[Dict[str, Any]]
    """Data field of the response data type for the /storage/select route."""

    @classmethod
    def get_records(cls, request: SelectRequest) -> SelectResponse:
        """Implements /storage/select route."""

        record_type = ClassInfo.get_class_type(f"{request.module}.{request.type_}")

        # Load records for type
        records = DbContext.get_db().load_all(record_type)  # noqa

        # Serialize records for table
        serialized_records = [ui_serializer.serialize_record_for_table(record) for record in records]

        # Get schema dict for type
        type_decl_dict = TypeResponseUtil.get_type(TypeRequest(name=request.type_, module=request.module, user="root"))

        return SelectResponse(schema=type_decl_dict, data=serialized_records)
