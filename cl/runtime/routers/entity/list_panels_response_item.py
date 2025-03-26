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
from typing import List
from pydantic import BaseModel
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.entity.list_panels_request import ListPanelsRequest
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.schema import Schema
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.serializers.key_serializers import KeySerializers

_KEY_SERIALIZER = KeySerializers.DELIMITED


class ListPanelsResponseItem(BaseModel):
    """Data type for a single item in the response list for the /entity/list_panels route."""

    name: str | None
    """Name of the panel."""

    type: str | None
    """Type of the record, e.g. Primary."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_response(cls, request: ListPanelsRequest) -> List[ListPanelsResponseItem]:
        """Implements /entity/list_panels route."""

        # TODO: Return saved view names
        request_type = Schema.get_type_by_short_name(request.type)

        # Get actual type from record if request.key is not None
        if request.key is not None:
            # Deserialize ui key
            key = _KEY_SERIALIZER.deserialize(request.key, request_type)

            # If the record is not found, display panel tabs for the base type
            record = DbContext.load_one_or_none(request_type, key)
            actual_type = request_type if record is None else type(record)
        else:
            actual_type = request_type

        # Get handlers from TypeDecl
        handlers = declare.handlers if (declare := TypeDecl.for_type(actual_type).declare) is not None else None

        if handlers is not None and handlers:
            return [
                ListPanelsResponseItem(name=handler.label, type=cls.get_type(handler))
                for handler in handlers
                if handler.type_ == "Viewer"
            ]
        return []

    @classmethod
    def get_type(cls, handler: HandlerDeclareDecl) -> str | None:
        """Get type of the handler."""

        if handler.type_ == "Viewer" and handler.name == "view_self":
            return "Primary"
