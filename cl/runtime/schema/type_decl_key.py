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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.schema.module_decl_key import ModuleDeclKey


@dataclass(slots=True, eq=False)
class TypeDeclKey(DataclassMixin, KeyMixin):
    """Provides information about a class, its fields, and its methods."""

    module: ModuleDeclKey = required()  # TODO: Merge with name to always use full name
    """Module reference."""

    name: str = required()
    """Type name is unique when combined with module."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return TypeDeclKey

    @classmethod
    def for_type(cls, type_: type) -> Self:
        """Create primitive type declaration from Python type."""
        return TypeDeclKey(module=ModuleDeclKey(), name=type_.__name__).build()
