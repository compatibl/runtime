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

import datetime as dt
from uuid import UUID
from cl.runtime.schema.module_decl_key import ModuleDeclKey
from cl.runtime.schema.type_decl_key import TypeDeclKey


class PrimitiveDeclKeys:
    """RatesSwapLegSideKey constants."""

    STR: TypeDeclKey = TypeDeclKey.from_type(str)
    """String primitive type."""

    FLOAT: TypeDeclKey = TypeDeclKey.from_type(float)
    """Float primitive type."""

    BOOL: TypeDeclKey = TypeDeclKey.from_type(bool)
    """Bool primitive type."""

    INT: TypeDeclKey = TypeDeclKey.from_type(int)
    """Int primitive type."""

    LONG: TypeDeclKey = TypeDeclKey(module=ModuleDeclKey(module_name=int.__module__), name="long")
    """Long primitive type, use builtins module with name=long"""

    DATE: TypeDeclKey = TypeDeclKey.from_type(dt.date)
    """Date primitive type."""

    TIME: TypeDeclKey = TypeDeclKey.from_type(dt.time)
    """Time primitive type."""

    DATETIME: TypeDeclKey = TypeDeclKey.from_type(dt.datetime)
    """Datetime primitive type."""

    UUID: TypeDeclKey = TypeDeclKey.from_type(UUID)
    """UUID primitive type."""

    bytes: TypeDeclKey = TypeDeclKey.from_type(bytes)
    """Bytes primitive type."""
