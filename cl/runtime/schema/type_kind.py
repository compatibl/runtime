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
    """Data type other than key or record, is_data returns True, is_key and is_record return False."""

    KEY = auto()
    """Key type (excludes records), is_key returns True."""

    RECORD = auto()
    """Record type (excludes keys), is_record returns True."""
