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
from enum import Enum
from typing import Type
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class EnumSerializer(Freezable):
    """Helper class for serialization and deserialization of enum types."""

    @classmethod
    def serialize(cls, value: Enum | None, enum_type: Type | None = None) -> TPrimitive | None:
        """Serialize an enum to a string or another primitive type (return None if value is None)."""
        # Check that type matches if specified
        if enum_type is not None and value is not None and type(value) is not enum_type:
            enum_type_name = TypeUtil.name(enum_type)
            raise ValueError(f"{value} is does not match the specified enum type {enum_type_name}")
        # Serialize as name without type in PascalCase
        return CaseUtil.upper_to_pascal_case(value.name) if value is not None else None

    @classmethod
    def deserialize(cls, value: TPrimitive | None, enum_type: Type) -> TPrimitive | None:
        """Deserialize a string or another primitive type to the specified enum type (return None if value is None)."""
        try:
            # Serialized value is name without type in PascalCase, convert to UPPER_CASE
            return enum_type[CaseUtil.pascal_to_upper_case(value)] if value is not None else None
        except KeyError:
            enum_type_name = TypeUtil.name(enum_type)
            raise ValueError(f"{value} is not a valid choice for enum type {enum_type_name}")
