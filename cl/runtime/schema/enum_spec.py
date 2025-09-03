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
from typing import Self
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.typename import typename
from cl.runtime.schema.enum_member_spec import EnumMemberSpec
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.schema.type_spec import TypeSpec


@dataclass(slots=True, kw_only=True)
class EnumSpec(TypeSpec):
    """Provides information about an enum type."""

    members: list[EnumMemberSpec] | None = None
    """List of enum members (use None for a placeholder enum with no members)."""

    @classmethod
    def for_type(cls, type_: type) -> Self:
        """Create from enum class."""

        # Check the argument is an enum
        if not issubclass(type_, Enum):
            raise RuntimeError(f"Cannot create {typename(cls)} from type {typename(type_)} because it is not an enum.")

        # Create the list of enum members
        members = [
            EnumMemberSpec(
                member_name=CaseUtil.upper_to_pascal_case(member.name),
            )
            for member in type_
        ]

        # Create the enum spec
        return EnumSpec(type_=type_, members=members).build()
