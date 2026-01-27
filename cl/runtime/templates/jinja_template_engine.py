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
from jinja2 import Environment
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.typename import typename, typenameof
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.templates.template_engine import TemplateEngine


@dataclass(slots=True, kw_only=True)
class JinjaTemplateEngine(TemplateEngine):
    """Uses Jinja2 engine to render the template."""

    def render(self, *, body: str, data: DataMixin | dict[str, Any]) -> str:
        """Render the template body by taking parameters from the data object or dict."""

        if isinstance(data, DataMixin):
            # Serialize data to dict if DataMixin
            data_dict = DataSerializers.DEFAULT.serialize(data)
        elif isinstance(data, dict):
            # Use as-is if a dict
            data_dict = data
        else:
            raise RuntimeError(
                f"Param 'data' in {typenameof(self)}.render(template, data) must be\n"
                f"a data object derived from DataMixin or a dict."
            )

        # Create Jinja2 environment with default {{ }} delimiters
        env = Environment(
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
        )

        # Create template from string and render with data
        body = env.from_string(body)
        result = body.render(data_dict)
        return result

