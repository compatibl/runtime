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
from memoization import cached
from cl.runtime.records.type_util import TypeUtil

_INHERITED_SLOTS = sys.version_info >= (3, 11)
"""In Python 3.11+, __slots__ from base are included in __slots__ of descendants."""


class SlotsUtil:
    """Helper methods for slots-based classes."""

    @classmethod
    @cached
    def get_slots(cls, data_type: type) -> Tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""

        if hasattr(data_type, "get_slots"):
            # Providing @classmethod get_slots makes it possible to serialize
            # a non-slotted class or override the default slots
            return data_type.get_slots()
        elif hasattr(data_type, "__slots__"):
            # Traverse the class hierarchy from base to derived (reverse MRO order) collecting slots as specified
            if _INHERITED_SLOTS:
                # For v3.11 and later, __slots__ includes fields for this class only, use MRO to collect
                # slots by traversing the entire class hierarchy, exclude None or empty __slots__ (both are falsy)
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

    @classmethod
    def merge_slots(cls, base: type, *slots: str) -> Tuple[str, ...]:
        """
        When not using any data class framework, merge slots from this class
        and base in a way that works for Python 3.10 where slots are not inherited
        and Python 3.11+ where they are.
        """
        if not _INHERITED_SLOTS:
            # Slots from base must be combined with the current class slots,
            # which must be present to avoid __dict__ but may be empty, e.g. ()
            base_slots = getattr(base, "__slots__")
            # __weakref__ should be explicitly filtered out(allowed only once in inheritance chain)
            filtered_base_slots = tuple(s for s in base_slots if s != "__weakref__")
            # Combine in the order of declaration from base to derived
            result = tuple(filtered_base_slots + slots)
        else:
            # Slots are merged automatically
            result = tuple(slots)
        return result
