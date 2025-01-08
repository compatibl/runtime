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
from dataclasses import dataclass
from dataclasses import fields
from typing import TypeGuard, Any
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import FreezableProtocol, _PRIMITIVE_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class Freezable(ABC):
    """
    Derive a dataclass from this base to add the ability to freeze from further modifications of its fields.
    Once frozen, the instance cannot be unfrozen. This affects only the speed of setters but not of getters.

    Notes:
        - This base should be used for dataclass objects, use the appropriate base for each framework
        - Use tuple which is immutable instead of list when deriving from this class
    """

    __frozen: bool = required(default=False, init=False)
    """
    Indicates the instance is frozen so its fields can no longer be modified.
    Once frozen, the instance cannot be unfrozen.
    """

    @classmethod
    def is_freezable(cls) -> TypeGuard[FreezableProtocol]:
        """
        Return True if the instance is freezable (implements freeze).
        For a class derived from this base, all mutable elements must also implement freeze.
        Among other things, this means such class can have tuple elements but not list elements.
        """
        return True

    def is_frozen(self) -> bool:
        """
        Return True if the object has already been frozen. Once frozen, the instance cannot be unfrozen.
        Non-freezable objects (objects with mutable elements that do not implement freeze) always return False.
        """
        return self.__frozen

    def freeze(self) -> None:
        """
        Traverse the object and call freeze for each mutable element. Once frozen, the instance cannot be unfrozen.
        Error message for non-freezable objects (objects with mutable elements that do not implement freeze).
        """

        # Freeze setting fields at root level
        object.__setattr__(self, "_Freezable__frozen", True)

        # Recursively call freeze on fields, except in case of tuple call freeze on tuple elements
        tuple(
            tuple(getattr(x, "freeze")() for x in field_value) if isinstance(field_value, tuple)
            else getattr(field_value, "freeze")() if type(field_value).__name__ not in _PRIMITIVE_TYPE_NAMES
            else None
            for field_obj in fields(self)  # noqa
            if (field_value := getattr(self, field_obj.name, None)) is not None
        )

    def __setattr__(self, key, value):
        """Raise an error if invoked for a frozen instance.."""
        if getattr(self, "_Freezable__frozen", False):
            raise AttributeError(f"Cannot modify field {TypeUtil.name(self)}.{key} because the object is frozen.")
        object.__setattr__(self, key, value)
