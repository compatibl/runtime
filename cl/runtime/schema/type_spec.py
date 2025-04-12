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
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.frozen_data import FrozenData
from cl.runtime.schema.type_kind import TypeKind


@dataclass(slots=True, kw_only=True, frozen=True)
class TypeSpec(FrozenData, ABC):
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    type_name: str
    """Unique type name (the same as class name except when alias is specified)."""

    type_kind: TypeKind
    """Type kind (primitive, enum, data, key, record)."""

    _class: type
    """Class where the type is stored (this is not the type hint as it excludes container and optional info)."""

    def get_class(self) -> type:
        """Class where the type is stored."""
        return self._class

    @classmethod
    @abstractmethod
    def from_class(cls, class_: type, subtype: str | None = None) -> Self:
        """Create spec from class, specify subtype only when different from class name (e.g., long or timestamp)."""
