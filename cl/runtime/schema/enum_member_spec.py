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
from enum import Enum
from typing import Literal
from typing import Type
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.container_decl import ContainerDecl
from cl.runtime.schema.container_kind_enum import ContainerKindEnum
from cl.runtime.schema.field_kind_enum import FieldKindEnum
from cl.runtime.schema.primitive_decl_keys import PrimitiveDeclKeys
from cl.runtime.schema.type_decl_key import TypeDeclKey


@dataclass(slots=True, kw_only=True)
class EnumMemberSpec(Freezable):
    """Provides information about a single member (item) of an enum."""

    member_name: str = required()
    """Name of the enum member (must be unique within the enum)."""
