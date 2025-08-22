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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.protocols import TData
from cl.runtime.templates.template_engine_key import TemplateEngineKey


@dataclass(slots=True, kw_only=True)
class TemplateEngine(TemplateEngineKey, RecordMixin, ABC):
    """Engine to perform template rendering."""

    def get_key(self) -> TemplateEngineKey:
        return TemplateEngineKey(engine_id=self.engine_id).build()

    @abstractmethod
    def render(self, text: str, data: TData) -> str:
        """Render the template text by taking parameters from the data."""
