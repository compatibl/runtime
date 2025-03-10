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
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.schema.container_kind_enum import ContainerKindEnum
from cl.runtime.schema.field_decl import FieldDecl
from cl.runtime.schema.field_kind_enum import FieldKindEnum
from cl.runtime.schema.member_decl import MemberDecl
from cl.runtime.schema.type_decl_key import TypeDeclKey
from cl.runtime.schema.value_decl import ValueDecl


@dataclass(slots=True, kw_only=True)
class ElementDecl(MemberDecl):  # TODO: Consider renaming to TypeFieldDecl or FieldDecl
    """Type element declaration."""

    name: str = required()
    """Element name."""

    label: str | None = None
    """Element label. If not specified, name is used instead."""

    comment: str | None = None
    """Element comment. Contains addition information."""

    vector: bool | None = None  # TODO: Replace by container field with enum values vector/array, dict, DF
    """Flag indicating variable size array (vector) container."""

    optional: bool | None = None
    """Flag indicating optional element."""

    optional_vector_element: bool | None = None  # TODO: Rename to optional_element or optional_field
    """Flag indicating optional vector item element."""

    read_only: bool | None = None
    """Flag indicating readonly element."""

    additive: bool | None = None
    """Optional flag indicating if the element is additive and that the total column can be shown in the UI."""

    format_: str | None = None  # TODO: Use Python interpolated string format
    """Specifies UI Format for the element."""

    alternate_of: str | None = None
    """Link current element to AlternateOf element. In the editor these elements will be treated as a choice."""

    @classmethod
    def create(cls, field_decl: FieldDecl) -> Self:
        """Create ElementDecl from FieldDecl."""

        result = ElementDecl()
        result.name = field_decl.name
        result.label = field_decl.label
        result.comment = field_decl.comment
        result.optional = field_decl.optional_field
        if field_decl.container is not None:
            result.optional_vector_element = field_decl.container.optional_items
        else:
            result.optional_vector_element = None
        result.additive = None  # TODO: Support in metadata
        result.format_ = field_decl.formatter
        result.alternate_of = None  # TODO: Support in metadata

        if field_decl.field_kind == FieldKindEnum.PRIMITIVE:
            # Primitive type
            result.value = ValueDecl.from_name(field_decl.field_type.name)
        else:
            # Complex type
            match field_decl.field_kind:
                case FieldKindEnum.ENUM:
                    result.enum = field_decl.field_type
                case FieldKindEnum.KEY:
                    result.key_ = TypeDeclKey(
                        module=field_decl.field_type.module,
                        name=field_decl.field_type.name  # .rstrip("Key")  # TODO: Check if Key suffix should be removed
                    ).build()
                case FieldKindEnum.DATA | FieldKindEnum.RECORD:
                    result.data = field_decl.field_type
                case _:
                    raise RuntimeError(f"Unsupported field kind {field_decl.field_kind.name} for field {field_decl.name}.")

        if field_decl.container is not None:
            match field_decl.container.container_kind:
                case ContainerKindEnum.LIST:
                    result.vector = True
                case ContainerKindEnum.DICT:
                    # TODO (Roman): This is legacy format, use another way to define the dict field
                    result.value = ValueDecl(type_="Dict")
                case _:
                    raise RuntimeError(f"Unsupported container kind {field_decl.container.container_kind.name} "
                                       f"for field {field_decl.name}.")
        else:
            result.vector = False

        return result
