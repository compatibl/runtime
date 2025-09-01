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
from typing import Self
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class PrimitiveSpec(TypeSpec):
    """Provides information about a primitive type."""

    @classmethod
    def from_class(cls, class_: type, subtype: str | None = None) -> Self:
        """Create spec from class, set name to subtype after checking compatibility."""
        if (class_name := class_.__name__) not in PRIMITIVE_TYPE_NAMES:
            primitive_class_names_str = ", ".join(PRIMITIVE_TYPE_NAMES)
            raise RuntimeError(f"Class {class_name} is not one of primitive types:\n{primitive_class_names_str}")
        if subtype is None:
            return PrimitiveSpec(type_name=class_name, type_kind=TypeKind.PRIMITIVE, type_=class_)
        else:
            if (
                # Supported combinations only
                (subtype == "long" and class_name == "int")
                or (subtype == "timestamp" and class_name == "str")
            ):
                return PrimitiveSpec(type_name=subtype, type_kind=TypeKind.PRIMITIVE, type_=class_)
            else:
                raise RuntimeError(f"Subtype {subtype} cannot be stored in class {class_name}.")
