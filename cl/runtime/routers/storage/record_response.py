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
from typing import cast
from pydantic import BaseModel
from pydantic import Field
from cl.runtime.backend.core.ui_type_state import UiTypeState
from cl.runtime.backend.core.ui_type_state_key import UiTypeStateKey
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil
from cl.runtime.routers.storage.record_request import RecordRequest
from cl.runtime.schema.field_decl import primitive_types  # TODO: Move definition to a separate module
from cl.runtime.schema.schema import Schema
from cl.runtime.serializers.string_serializer import StringSerializer
from cl.runtime.serializers.ui_dict_serializer import UiDictSerializer

key_serializer = StringSerializer()
ui_serializer = UiDictSerializer()


class RecordResponse(BaseModel):
    """Response data type for the /storage/record route."""

    schema_: Dict[str, Any] = Field(..., alias="schema")
    """Schema field of the response data type for the /storage/record route."""

    data: Dict[str, Any] | None
    """Data field of the response data type for the /storage/record route."""

    @classmethod
    def get_record(cls, request: RecordRequest) -> RecordResponse:
        """Implements /storage/record route."""

        record_type = Schema.get_type_by_short_name(request.type)
        deserialized_key = key_serializer.deserialize_key(request.key, record_type.get_key_type()).build()

        # TODO: Review the use of load_one_or_none here
        record = DbContext.get_db().load_one_or_none(record_type, deserialized_key)

        # Pin all handlers by default
        if not record and record_type == UiTypeState:
            # TODO (Yauheni): remove temporary workaround of pinning handlers for all requested types
            deserialized_key = cast(UiTypeStateKey, deserialized_key)
            record = cls._get_default_ui_type_state(deserialized_key)

        # Get type declarations based on the actual record type
        type_decl_dict = (
            TypeResponseUtil.get_type(
                TypeRequest(
                    name=type(record).__name__,
                    module=request.module,
                    user="root",
                ),
            )
            if record is not None
            else dict()
        )  # Handle not found record

        # Serialize record to ui format
        # TODO: Optimize speed
        record_dict = ui_serializer.serialize_data(record)

        return RecordResponse(schema=type_decl_dict, data=record_dict)

    @classmethod
    def _get_default_ui_type_state(cls, ui_type_state_requested_key: UiTypeStateKey) -> UiTypeState:
        """Return default UiTypeState with pinned all handlers."""

        type_state_record_type = Schema.get_type_by_short_name(ui_type_state_requested_key.type_.name)
        type_state_record_type_schema = Schema.for_type(type_state_record_type)

        # Iterate over type declarations to get all handlers
        all_handlers = []
        for decl_dict in type_state_record_type_schema.values():
            declare_block = decl_dict.get("Declare")
            if not declare_block:
                continue

            handlers_block = declare_block.get("Handlers")
            if not handlers_block:
                continue

            all_handlers.extend(
                [
                    handler_name
                    for handler_decl in handlers_block
                    if (handler_name := handler_decl.get("Name")) not in all_handlers
                ]
            )

        return UiTypeState(
            user=ui_type_state_requested_key.user,
            type_=ui_type_state_requested_key.type_,
            pinned_handlers=all_handlers,
        )
