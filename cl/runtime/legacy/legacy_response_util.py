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
from cl.runtime.records.protocols import is_primitive


class LegacyResponseUtil:
    """Util class to convert response data to legacy format."""

    @classmethod
    def _replace_with_legacy_model(cls, data_dict: Dict) -> Dict[str, Any]:
        """Convert data dict to legacy model."""

        if not (_t := data_dict.get("_t")):
            return data_dict

        if _t == "PngView":
            return {"FileBytes": data_dict.get("PngBytes"), "FileType": "Png", "_t": "FileData"}
        elif _t == "HtmlView":
            return {
                "FileBytes": data_dict.get("HtmlBytes"),
                "FileType": "Html",
                "_t": "FileData",
            }
        elif _t == "PdfView":
            return {
                "FileBytes": data_dict.get("PdfBytes"),
                "FileType": "Pdf",
                "_t": "FileData",
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

        if is_primitive(data):
            return data
        elif isinstance(data, dict):
            return {k: cls._format_data(v) for k, v in cls._replace_with_legacy_model(data).items()}
        elif hasattr(data, "__iter__"):
            return type(data)(cls._format_data(x) for x in data)
        else:
            return data

    @classmethod
    def format_panel_response(cls, panel_response: dict[str, Any]) -> dict[str, Any]:
        """Format /get_panel response to legacy format."""

        return {"ViewOf": cls._format_data(panel_response)}
