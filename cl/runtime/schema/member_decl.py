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
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.schema.type_decl_key import TypeDeclKey
from cl.runtime.schema.value_decl import ValueDecl


@dataclass(slots=True, kw_only=True)
class MemberDecl(DataclassMixin):
    """Type member declaration."""

    value: ValueDecl | None = None  # TODO: Flatten value and other types to a single field
    """Value or primitive element declaration."""

    enum: TypeDeclKey | None = None
    """Enumeration element declaration."""

    data: TypeDeclKey | None = None
    """Data element declaration."""

    key_: TypeDeclKey | None = None  # TODO: It is no longer necessary to add _ to key field
    """Key element declaration."""

    query: TypeDeclKey | None = None
    """Query element declaration."""

    condition: TypeDeclKey | None = None
    """Condition element declaration."""
