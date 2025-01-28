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
from typing_extensions import Self
from cl.runtime.records.build_mixin import BuildMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class Freezable(BuildMixin, ABC):
    """
    Derive a dataclass from this base to add the ability to freeze from further modifications of its fields.
    Once frozen, the instance cannot be unfrozen. This affects only the speed of setters but not of getters.

    Notes:
        - This base should be used for dataclass objects, use the appropriate base for each framework
        - Use tuple which is immutable instead of list when deriving from this class
    """

    _frozen: bool = required(default=False, init=False, repr=False, compare=False)
    """True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        return self._frozen

    def check_frozen(self, action_str: str | None = None) -> None:
        """Error message if the instance is not frozen."""
        if not self._frozen:
            action_str = action_str if action_str else "using or performing setup"
            raise RuntimeError(f"Freeze {TypeUtil.name(self)} before {action_str}.")

    def freeze(self) -> Self:
        """
        Freeze the instance without recursively calling freeze on its fields. Return self for method chaining.
        Once frozen, the instance cannot be unfrozen.
        """
        object.__setattr__(self, "_frozen", True)
        return self

    def __setattr__(self, key, value):
        """Raise an error on attempt to modify a public field for a frozen instance."""
        if getattr(self, "_frozen", False) and not key.startswith("_"):
            raise RuntimeError(
                f"Cannot modify public field {TypeUtil.name(self)}.{key} " f"because the instance is frozen."
            )
        object.__setattr__(self, key, value)
