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
from typing import List
from typing import Type
from typing_extensions import Self
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.schema.enum_member_spec import EnumMemberSpec
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True, frozen=True)
class EnumSpec(TypeSpec):
    """Provides information about an enum type."""

    members: List[EnumMemberSpec] | None = None
    """List of enum members (use None for a placeholder enum with no members)."""

    @classmethod
    def from_class(cls, class_: Type, subtype: str | None = None) -> Self:
        """Create spec from class, subtype is not permitted."""

        # Perform checks
        class_name = class_.__name__
        if not issubclass(class_, Enum):
            raise RuntimeError(f"Cannot create EnumSpec for {class_name} because it is not an enum.")
        if subtype is not None:
            raise RuntimeError(
                f"Subtype {subtype} is specified for enum class {class_name}.\n"
                f"Only primitive types can have subtypes."
            )

        # Create the list of enum members
        members = [
            EnumMemberSpec(
                member_name=CaseUtil.upper_to_pascal_case(member.name),
            )
            for member in class_
        ]

        # Create the enum spec
        result = EnumSpec(type_name=class_name, _class=class_, members=members)
        return result
