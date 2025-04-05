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

import types
import typing
from dataclasses import dataclass
from typing import Type
from uuid import UUID

from frozendict import frozendict
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.frozen_data_mixin import FrozenDataMixin
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES, SEQUENCE_TYPE_NAMES, MAPPING_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True, frozen=True)
class TypeHint(FrozenDataMixin):
    """Provides information about a type hint."""

    schema_type_name: str
    """Type name in the schema."""

    schema_class: Type | None = None
    """Class if available, if not provided it will be looked up using the type name."""

    optional: bool | None = None
    """Optional flag, True if the type hint is a union with None, None otherwise."""

    remaining: Self | None = None
    """Remaining chain if present, None otherwise."""

    def to_str(self):
        """Serialize as string in type alias format."""
        if self.remaining is not None:
            if self.optional:
                return f"{self.schema_type_name}[{self.remaining.to_str()}] | None"
            else:
                return f"{self.schema_type_name}[{self.remaining.to_str()}]"
        else:
            if self.optional:
                return f"{self.schema_type_name} | None"
            else:
                return f"{self.schema_type_name}"

    def validate_for_sequence(self) -> None:
        """Raise an error if the type hint is not a sequence."""
        if not self.schema_type_name in SEQUENCE_TYPE_NAMES:
            raise RuntimeError(f"The data is a sequence but type hint {self.to_str()} does not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a sequence type but does not specify item type.")

    def validate_for_mapping(self) -> None:
        """Raise an error if the type hint is not a mapping."""
        if not self.schema_type_name in MAPPING_TYPE_NAMES:
            raise RuntimeError(f"The data is a mapping but type hint {self.to_str()} does not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a mapping but does not specify item type.")

    @classmethod
    def for_class(cls, class_: Type, *, is_optional: bool | None = None) -> Self:
        return cls(
            schema_type_name=class_.__name__,
            schema_class=class_,
            optional=is_optional,
        )
