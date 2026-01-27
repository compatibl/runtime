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

from dataclasses import dataclass
from typing import Any
from box import Box
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.typename import typenameof
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.templates.template_engine import TemplateEngine


@dataclass(slots=True, kw_only=True)
class FstringTemplateEngine(TemplateEngine):
    """Uses Python f-string engine to render the template."""

    def render(self, *, body: str, data: DataMixin | dict[str, Any]) -> str:
        """Render the template body by taking parameters from the data object or dict."""

        if isinstance(data, DataMixin):
            # Serialize data to dict if DataMixin
            data_dict = DataSerializers.DEFAULT.serialize(data)
        elif isinstance(data, dict):
            # Otherwise keep as dict
            data_dict = data
        else:
            raise RuntimeError(
                f"Param 'data' in {typenameof(self)}.render(template, data) must be\n"
                f"a data object derived from DataMixin or a dict."
            )

        # Wrap into Box to permit both dot notation and dictionary field access at every level
        data_dict = Box(data_dict)

        # Serialize data to dict if DataMixin, otherwise use as-is, then wrap in Box for dot notation access
        # data_dict = Box(DataSerializers.DEFAULT.serialize(data) if isinstance(data, DataMixin) else data)
        result = str.format(body.format_map(data_dict))
        return result
