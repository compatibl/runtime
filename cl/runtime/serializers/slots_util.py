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

import sys
from collections import Counter
from typing import Tuple
from typing import Type
from typing import cast
from memoization import cached
from cl.runtime.records.type_util import TypeUtil

_COLLECT_SLOTS = sys.version_info.major > 3 or sys.version_info.major == 3 and sys.version_info.minor >= 11
"""For Python 3.11 and later, __slots__ includes fields for this class only, use MRO to include base class slots."""


class SlotsUtil:
    """Helper methods for slots-based classes."""

    @classmethod
    @cached
    def get_slots(cls, data_type: Type) -> Tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""

        # Traverse the class hierarchy from base to derived (reverse MRO order) collecting slots as specified
        if _COLLECT_SLOTS:
            # For v3.11 and later, __slots__ includes fields for this class only, use MRO to collect base class slots
            # Exclude None or empty __slots__ (both are falsy)
            class_hierarchy_slots = [
                slots for base in reversed(data_type.__mro__) if (slots := getattr(base, "__slots__", None))
            ]
        else:
            # Otherwise get slots from this type only
            # Exclude None or empty __slots__ (both are falsy)
            class_hierarchy_slots = [slots if (slots := getattr(data_type, "__slots__", None)) else tuple()]

        # Exclude empty tuples and convert slots specified as a single string into tuple of size one
        class_hierarchy_slots = [(slots,) if isinstance(slots, str) else slots for slots in class_hierarchy_slots]

        # Flatten and convert to tuple, cast relies on elements of sublist being strings
        # Exclude private and protected fields
        result = tuple(slot for sublist in class_hierarchy_slots for slot in sublist if not slot.startswith("_"))

        # Check for duplicates
        if len(result) > len(set(result)):
            # Error message if duplicates are found
            counts = Counter(result)
            duplicates = [slot for slot, count in counts.items() if count > 1]
            duplicates_str = ", ".join(duplicates)
            raise RuntimeError(
                f"Duplicate field names found in class hierarchy " f"for {TypeUtil.name(data_type)}: {duplicates_str}."
            )

        return result

