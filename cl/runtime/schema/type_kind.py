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

from enum import IntEnum
from enum import auto


class TypeKind(IntEnum):
    """Type kind (primitive, enum, data, key, record)."""

    PRIMITIVE = auto()
    """Primitive type."""

    ENUM = auto()
    """Enum type (must be derived from IntEnum), is_enum returns True."""

    DATA = auto()
    """Data type (excludes keys and records), is_data returns True."""

    KEY = auto()
    """Key type (excludes records even if they are derived from key), is_key returns True."""

    RECORD = auto()
    """Record type, is_record returns True."""

    MIXIN = auto()
    """Abstract mixin type (excludes classes derived from the mixin), is_mixin returns True."""

    PROTOCOL = auto()
    """Abstract protocol type (excludes classes implementing the protocol), is_protocol returns True."""

    ANY = auto()
    """Any type (includes all other types), is_any returns True."""

