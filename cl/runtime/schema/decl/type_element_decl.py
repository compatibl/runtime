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

from cl.runtime.decorators.attrs_data_decorator import attrs_data
from typing import List, Optional

from cl.runtime.schema.decl.element_modification_type import ElementModificationType
from cl.runtime.schema.decl.type_member_decl import TypeMemberDecl
from cl.runtime.decorators.data_field_decorator import data_field


@attrs_data
class TypeElementDecl(TypeMemberDecl):
    """Type element declaration."""

    name: str = data_field()
    """Element name."""

    label: Optional[str] = data_field()
    """Element label. If not specified, name is used instead."""

    comment: Optional[str] = data_field()
    """Element comment. Contains addition information."""

    vector: Optional[bool] = data_field()
    """Flag indicating variable size array (vector) container."""

    aliases: Optional[List[str]] = data_field()
    """Element aliases."""

    optional: Optional[bool] = data_field()
    """Flag indicating optional element."""

    optional_vector_element: Optional[bool] = data_field()
    """Flag indicating optional vector item element."""

    secure: Optional[bool] = data_field()
    """Secure flag."""

    filterable: Optional[bool] = data_field()
    """Flag indicating filterable element."""

    read_only: Optional[bool] = data_field()
    """Flag indicating readonly element."""

    hidden: Optional[bool] = data_field()
    """Flag indicating a hidden element. Hidden elements are visible in API but not in the UI."""

    additive: Optional[bool] = data_field()
    """Optional flag indicating if the element is additive and that the total column can be shown in the UI."""

    category: Optional[str] = data_field()
    """Category."""

    format_: Optional[str] = data_field(name='Format')
    """Specifies UI Format for the element."""

    output: Optional[bool] = data_field()
    """Flag indicating output element. These elements will be readonly in UI and can be fulfilled by handlers."""

    alternate_of: Optional[str] = data_field()
    """Link current element to AlternateOf element. In the editor these elements will be treated as a choice."""

    viewer: Optional[str] = data_field()
    """The element will be viewed under specified tab."""

    modification_type: Optional[ElementModificationType] = data_field()
    """Element Modification Type."""