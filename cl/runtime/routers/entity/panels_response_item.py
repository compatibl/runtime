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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.routers.entity.panels_request import PanelsRequest
from cl.runtime.schema.handler_declare_decl import HandlerDeclareDecl
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.views.view_persistence_util import ViewPersistenceUtil

_KEY_SERIALIZER = KeySerializers.DELIMITED


class PanelsResponseItem(BaseModel):
    """Data type for a single item in the response list for the /entity/panels route."""

    name: str | None
    """Name of the panel."""

    kind: str | None
    """Type of the record, e.g. Primary."""

    persistable: bool | None
    """Whether the panel is persistent."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_response(cls, request: PanelsRequest) -> list[PanelsResponseItem]:
        """Implements /entity/panels route."""

        record_type = TypeInfo.from_type_name(request.type_name)
        key_type = record_type.get_key_type()

        persisted_views = []

        # Get actual type from record if request.key is not None
        if request.key is not None:
            # Deserialize ui key
            key = _KEY_SERIALIZER.deserialize(request.key, TypeHint.for_type(key_type))

            # If the record is not found, display panel tabs for the base type
            record = active(DataSource).load_one_or_none(key)
            actual_type = record_type if record is None else type(record)
            if record is not None:
                # Get persisted views for this record
                persisted_views = ViewPersistenceUtil.load_all_views_for_record(record)
        else:
            actual_type = record_type

        # Get handlers from TypeDecl
        handlers = declare.handlers if (declare := TypeDecl.for_type(actual_type).declare) is not None else None

        result = [
            PanelsResponseItem(
                name=persisted_view.view_name,
                kind=ViewPersistenceUtil.get_panel_kind_from_view(persisted_view),
                persistable=True,
            )
            for persisted_view in persisted_views
        ]

        if handlers:
            result += [
                PanelsResponseItem(
                    name=handler.label,
                    kind=cls.get_panel_kind(handler),
                    persistable=False,
                )
                for handler in handlers
                if handler.type_ == "Viewer"
            ]
        return result

    @classmethod
    def get_panel_kind(cls, handler: HandlerDeclareDecl) -> str | None:
        """Get type of the handler."""

        if handler.type_ == "Viewer" and handler.name == "view_self":
            return "Primary"
