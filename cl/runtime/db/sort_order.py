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


class SortOrder(IntEnum):
    """Sort order for database queries and other methods that return a sequence result."""

    UNORDERED = auto()
    """Not sorted and can be returned in implementation-dependent order."""

    ASC = auto()
    """Sorted in ascending order."""

    DESC = auto()
    """Sorted in descending order."""

    INPUT = auto()
    """Sorted in the order of the input sequence, if such a parameter exists and has the same length as the result."""
