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

from typing import Any, Dict

from cl.runtime.routers.entity.panel_response_util import PanelResponseData


class LegacyResponseUtil:
    """Util class to convert response data to legacy format."""

    @classmethod
    def _replace_with_legacy_model(cls, data_dict: Dict) -> Dict[str, Any]:
        """Convert data dict to legacy model."""

        if not (_t := data_dict.get("_t")):
            return data_dict

        if _t == "PngView":
            return {
                "Content": data_dict.get("PngBytes"),
                "ContentType": "Png",
                "_t": "BinaryContent"
            }
        elif _t == "HtmlView":
            return {
                "Content": data_dict.get("HtmlBytes"),
                "ContentType": "Html",
                "_t": "BinaryContent",
            }
        elif _t == "PdfView":
            return {
                "Content": data_dict.get("PdfBytes"),
                "ContentType": "Pdf",
                "_t": "BinaryContent",
            }
        elif _t == "Dag":
            return {**data_dict, "_t": "DAG"}
        elif _t == "Script":
            return {**data_dict, "Language": data_dict.get("Language").capitalize()}
        else:
            return data_dict

    @classmethod
    def _format_data(cls, data):
        """Format data object to legacy format."""

        if isinstance(data, dict):
            return {k: cls._format_data(v) for k, v in cls._replace_with_legacy_model(data).items()}
        if hasattr(data, "__iter__"):
            return type(data)(cls._format_data(x) for x in data)
        else:
            return data

    @classmethod
    def format_panel_response(cls, panel_response: Dict[str, PanelResponseData]) -> Dict[str, PanelResponseData]:
        """Format /get_panel response to legacy format."""

        return {k: {"ViewOf": cls._format_data(v)} for k, v in panel_response.items()}



