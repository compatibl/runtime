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

from typing import Any
from typing import Dict
from typing import List
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.log.log_message import LogMessage
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.schema.schema import Schema
from cl.runtime.schema.type_decl import TypeDecl
from cl.runtime.serializers.string_serializer import StringSerializer
from cl.runtime.serializers.ui_dict_serializer import UiDictSerializer

PanelResponseDataItem = Dict[str, Any]
PanelResponse = Dict[str, PanelResponseDataItem | List[PanelResponseDataItem] | None]

# Create serializers
ui_serializer = UiDictSerializer()
key_serializer = StringSerializer()


class PanelResponseUtil:
    """Response util for the /entity/panel route."""

    @classmethod
    def _get_content(cls, request: PanelRequest) -> PanelResponse:
        """Implements /entity/panel route."""

        # Get type of the record
        type_ = Schema.get_type_by_short_name(request.type)

        # Deserialize key from string to object
        key_obj = key_serializer.deserialize_key(request.key, type_.get_key_type()).build()

        # Get database from the current context
        db = DbContext.get_db()

        # Load record from the database
        record = db.load_one(type_, key_obj, dataset=request.dataset)
        if record is None:
            raise RuntimeError(
                f"Record with type {request.type} and key {request.key} is not found in dataset {request.dataset}."
            )

        # Check if the selected type has the needed viewer and get its name (only viewer's label is provided)

        # Get handlers from TypeDecl
        handlers = declare.handlers if (declare := TypeDecl.for_type(type(record)).declare) is not None else None

        if not handlers or not (
            viewer_name := next((h.name for h in handlers if h.label == request.panel_id and h.type_ == "Viewer"), None)
        ):
            raise RuntimeError(f"Type {TypeUtil.name(record)} has no view named '{request.panel_id}'.")

        # Call the viewer and get the result
        viewer = getattr(record, viewer_name)
        view = viewer()

        return ui_serializer.serialize_data(view)

    @classmethod
    def get_response(cls, request: PanelRequest) -> PanelResponse:

        try:
            return cls._get_content(request)
        except Exception as e:
            # TODO (Roman): Improve main error handler
            DbContext.save_one(LogMessage(message=str(e)).build())
            return {  # TODO: Refactor
                "_t": "Script",
                "Name": None,
                "Language": "Markdown",
                "Body": ["## The following error occurred during the rendering of this view:\n", f"{str(e)}"],
                "WordWrap": True,
            }
