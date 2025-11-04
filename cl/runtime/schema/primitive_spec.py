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
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typenameof
from cl.runtime.schema.field_decl import primitive_types
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class PrimitiveSpec(TypeSpec):
    """Provides information about a primitive type."""

    subtype: str | None
    """Subtype (e.g., long) if specified, None otherwise."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Check that type_ is primitive
        if not is_primitive_type(self.type_):
            primitive_type_names_str = ", ".join(PRIMITIVE_TYPE_NAMES)
            raise RuntimeError(
                f"Cannot create an instance of {typename(type(self))} for type {typenameof(self.type_)}\n"
                f"because it is not one of the supported primitive types:\n{primitive_type_names_str}"
            )

        # Check subtype compatibility
        if not (
            # Supported combinations only
            self.subtype is None
            or (self.type_ is int and self.subtype == "long")
            or (self.type_ is str and self.subtype == "timestamp")
        ):
            raise RuntimeError(f"Subtype {self.subtype} cannot be stored in class {type_name}.")
