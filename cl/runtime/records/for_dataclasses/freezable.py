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

from abc import ABC
from dataclasses import dataclass, fields
from dataclasses import field


@dataclass(slots=True, kw_only=True)
class Freezable(ABC):
    """
    Derive a dataclass from this base to add the ability to freeze from further modifications of its fields.
    Once frozen, the instance cannot be unfrozen. This affects only the speed of setters but not of getters.

    Notes:
        This base should be used for dataclass objects, use the appropriate base for each framework.
    """

    __frozen: bool = field(default=False, init=False)
    """
    Indicates the instance is frozen so its fields can no longer be modified.
    Once frozen, the instance cannot be unfrozen.
    """

    def is_frozen(self) -> bool:
        """Check if the instance has been frozen by calling its freeze method."""
        return self.__frozen

    def freeze(self) -> None:
        """
        Freeze setting fields at root level and invoke freeze method for those field types that implement it.
        This will not prevent in-place modification of mutable field types that do not implement freeze.
        Once frozen, the instance cannot be unfrozen.
        """

        # Freeze setting fields at root level
        object.__setattr__(self, "_Freezable__frozen", True)

        # Recursively call freeze on those field types that implement it
        tuple(
            field_freeze() for field_obj in fields(self)  # noqa
            if (field_value := getattr(self, field_obj.name, None)) is not None
            and (field_freeze := getattr(field_value, "freeze", None)) is not None
        )

    def __setattr__(self, key, value):
        """Raise an error if invoked for a frozen instance.."""
        if getattr(self, "_Freezable__frozen", False):
            raise AttributeError(f"Cannot modify field {type(self).__name__}.{key} because the object is frozen.")
        object.__setattr__(self, key, value)
