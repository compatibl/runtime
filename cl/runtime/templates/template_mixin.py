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
from typing import Generic
from typing import TypeVar
from cl.runtime import RecordMixin
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.records.protocols import TKey
from cl.runtime.templates.template_engine import TemplateEngine
from cl.runtime.templates.template_engine_key import TemplateEngineKey

TParams = TypeVar("TParams")


class TemplateMixin(Generic[TKey, TParams], RecordMixin[TKey], ABC):
    """
    Optional generic mixin for a template parameterized by its key and the parameters data type.
    Derive MyTemplate from MyTemplate(MyKey, TemplateMixin[MyKey, TParams]).
    """

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @property
    @abstractmethod
    def body(self) -> str:
        """Template body before parameter substitution."""

    @property
    @abstractmethod
    def engine(self) -> TemplateEngineKey:
        """Template engine used to render the template."""

    def render(self, data: TParams) -> str:
        """Render the template by substituting parameters from the specified data object."""
        engine = DbContext.load_one(TemplateEngine, self.engine)
        result = engine.render(self.body, data)
        return result
