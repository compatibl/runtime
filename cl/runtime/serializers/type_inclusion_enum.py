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


class TypeInclusionEnum(IntEnum):
    """Where to include type information in serialized data."""

    OMIT = auto()
    """Do not include type information in serialized data, deserialization is not possible."""

    AS_NEEDED = auto()
    """Always include type information at root level, include at other levels as needed."""

    ALWAYS = auto()
    """Always include type information in serialized data at all levels."""
