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
from memoization import cached
from cl.runtime.records.type_util import TypeUtil

# We rely on __slots__ from base being included in __slots__ of descendants in Python 3.11+
if sys.version_info < (3, 11):
    raise RuntimeError(
        f"We rely on __slots__ from base being included in __slots__ of descendants.\n"
        f"This feature requires Python 3.11+, while this version is: "
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )


class SlotsUtil:
    """Helper methods for slots-based classes."""

    @classmethod
    @cached
    def get_slots(cls, data_type: type) -> tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""

        if hasattr(data_type, "__slots__"):
            # Use MRO to collect slots by traversing the entire class hierarchy,
            # exclude None or empty __slots__ (both are falsy)
            class_hierarchy_slots = [
                slots for base in reversed(data_type.__mro__) if (slots := getattr(base, "__slots__", None))
            ]

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
                    f"Duplicate field names found in class hierarchy "
                    f"for {TypeUtil.name(data_type)}: {duplicates_str}."
                )
            return result
        else:
            # Error message if no __slots__ attribute is found
            raise RuntimeError(
                f"Class {TypeUtil.name(data_type)} cannot be serialized because it does not have\n"
                f"the '__slots__' attribute and does not define a custom @classmethod 'get_slots'."
            )
