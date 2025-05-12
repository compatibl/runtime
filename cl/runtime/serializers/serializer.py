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
from typing import Any
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.schema.type_hint import TypeHint


@dataclass(slots=True, kw_only=True, frozen=True)
class Serializer(BootstrapMixin, ABC):
    """Abstract base class of serializers that convert from one data representation to another."""

    @abstractmethod
    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary."""

    @abstractmethod
    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a dictionary into object using type information extracted from the _type field."""
