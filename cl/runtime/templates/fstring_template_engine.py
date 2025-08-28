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
from box import Box
from cl.runtime.records.data_mixin import TData
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.templates.template_engine import TemplateEngine


@dataclass(slots=True, kw_only=True)
class FstringTemplateEngine(TemplateEngine):
    """Uses Python f-string engine to render the template."""

    def render(self, text: str, data: TData) -> str:
        """Render the template text by taking parameters from the data."""
        # TODO: Add validation
        data_dict = Box(DataSerializers.DEFAULT.serialize(data))
        result = str.format(text.format_map(data_dict))
        return result
