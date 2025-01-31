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
from typing import Dict, Any

from cl.runtime.contexts.db_context import DbContext
from cl.runtime.plots.plot_key import PlotKey
from cl.runtime.routers.entity.panel_response_util import ui_serializer
from cl.runtime.view.dag.dag import Dag
from cl.runtime.views.html_view import HtmlView
from cl.runtime.views.key_view import KeyView
from cl.runtime.views.pdf_view import PdfView
from cl.runtime.views.plot_view import PlotView
from cl.runtime.views.png_view import PngView
from cl.runtime.views.script import Script


class LegacyFormatUtil:

    # TODO (Roman): Separate serialization and converting to legacy format logic
    @classmethod
    def get_legacy_format_view(cls, view: Any) -> Dict[str, Any]:
        # Return None if view is None
        if view is None:
            return None

        if isinstance(view, PlotView):
            # Load plot for view if it is key
            plot = DbContext.load_one(PlotKey, view.plot)
            if plot is None:
                raise RuntimeError(f"Not found plot for key {view.plot}.")

            # Get view for plot and transform to ui format dict
            return cls.get_legacy_format_view(plot.get_view())

        elif isinstance(view, KeyView):
            # Load record for view
            record = DbContext.load_one(type(view.key), view.key)
            if record is None:
                raise RuntimeError(f"Not found record for key {view.key}.")

            # Return ui format dict dict of record
            return cls.get_legacy_format_view(record)

        elif isinstance(view, PngView):
            # Return ui format dict of binary data
            return {
                "Content": base64.b64encode(view.png_bytes).decode(),
                "ContentType": "Png",
                "_t": "BinaryContent",
            }
        elif isinstance(view, HtmlView):
            # Return ui format dict of binary data
            return {
                "Content": base64.b64encode(view.html_bytes).decode(),
                "ContentType": "Html",
                "_t": "BinaryContent",
            }
        elif isinstance(view, PdfView):
            # Return ui format dict of binary PDF view data
            return {
                "Content": base64.b64encode(view.pdf_bytes).decode(),
                "ContentType": "Pdf",
                "_t": "BinaryContent",
            }
        elif isinstance(view, Dag):
            # Serialize Dag using ui serialization
            view_dict = ui_serializer.serialize_data(view)

            # Set _t with legacy Dag type name
            view_dict["_t"] = "DAG"

            # Return Dag view
            return view_dict
        elif isinstance(view, Script):
            # Return script
            view_dict: dict = ui_serializer.serialize_data(view)
            view_dict["Language"] = view_dict.pop("Language").capitalize()
            return view_dict
        elif isinstance(view, Dict):
            # Return if is already dict
            return view
        else:
            # TODO (Ina): Do not use a method from dataclasses
            result_type = type(view)
            view_dict = ui_serializer.serialize_data(view)
            view_dict["_t"] = result_type.__name__
            return view_dict
