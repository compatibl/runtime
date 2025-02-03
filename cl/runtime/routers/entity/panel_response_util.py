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

import base64
from typing import Any
from typing import Dict
from typing import List
from pydantic import BaseModel
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.plots.plot_key import PlotKey
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.schema.handler_declare_block_decl import HandlerDeclareBlockDecl
from cl.runtime.schema.schema import Schema
from cl.runtime.serialization.string_serializer import StringSerializer
from cl.runtime.serialization.ui_dict_serializer import UiDictSerializer
from cl.runtime.view.dag.dag import Dag
from cl.runtime.views.html_view import HtmlView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.pdf_view import PdfView
from cl.runtime.views.plot_view import PlotView
from cl.runtime.views.png_view import PngView
from cl.runtime.views.script import Script

PanelResponseData = Dict[str, Any] | List[Dict[str, Any]] | None


ui_serializer = UiDictSerializer()
"""Ui serializer."""


class PanelResponseUtil(BaseModel):
    """Response util for the /entity/panel route."""

    @classmethod
    def get_content(cls, request: PanelRequest) -> Dict[str, PanelResponseData]:
        """Implements /entity/panel route."""

        # Get type of the record
        type_ = Schema.get_type_by_short_name(request.type)

        # Deserialize key from string to object
        serializer = StringSerializer()
        key_obj = serializer.deserialize_key(request.key, type_.get_key_type()).build()

        # Get database from the current context
        db = DbContext.get_db()

        # Load record from the database
        record = db.load_one(type_, key_obj, dataset=request.dataset)
        record_type = type(record)
        if record is None:
            raise RuntimeError(
                f"Record with type {request.type} and key {request.key} is not found in dataset {request.dataset}."
            )

        # Check if the selected type has the needed viewer and get its name (only viewer's label is provided)
        handlers = HandlerDeclareBlockDecl.get_type_methods(record_type, inherit=True).handlers
        if (
            handlers is not None
            and handlers
            and (found_viewers := [h.name for h in handlers if h.label == request.panel_id and h.type_ == "Viewer"])
        ):
            viewer_name: str = found_viewers[0]
        else:
            raise Exception(f"Type {TypeUtil.name(record_type)} has no view with the name {request.panel_id}.")

        # Call the viewer and get the result
        viewer = getattr(record, viewer_name)
        return viewer()
