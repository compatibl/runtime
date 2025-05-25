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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.templates.template_engine_key import TemplateEngineKey
from cl.runtime.templates.template_mixin import TemplateMixin
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime.templates.stub_template_key import StubTemplateKey


@dataclass(slots=True, kw_only=True)
class StubTemplate(StubTemplateKey, TemplateMixin[StubTemplateKey, StubDataclassNestedFields]):
    """Interest rate swap trade template."""

    engine: TemplateEngineKey = required()
    """Template engine used for rendering."""

    def get_key(self) -> StubTemplateKey:
        return StubTemplateKey(body=self.body).build()
