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
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec


@dataclass(slots=True, kw_only=True)
class NoSlotsSpec(DataSpec):
    """Provides information about a class with no slots."""

    @classmethod
    def from_class(cls, class_: type, subtype: str | None = None) -> Self:
        """Create spec from class, subtype is not permitted."""

        # This class (NoSlotsSpec) is only appropriate for a data base or mixin class that does not define its own slots
        type_name = typename(class_)
        if not is_data_key_or_record(class_):
            raise RuntimeError(
                f"Cannot create {cls.__name__} for class {type_name} because it is not data, key or record."
            )
        elif class_.get_field_names():
            raise RuntimeError(f"Cannot create {cls.__name__} for class {type_name} because it has slots.")

        # Subtypes are only for primitive types
        if subtype is not None:
            raise RuntimeError(
                f"Subtype {subtype} is specified for non-primitive class {type_name}.\n"
                f"Only primitive types can have subtypes."
            )

        result = NoSlotsSpec(
            type_name=type_name,
            type_=class_,
            fields=[],
        ).build()
        return result
