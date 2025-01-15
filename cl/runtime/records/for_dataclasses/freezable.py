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
from cl.runtime.records.build_what_enum import BuildWhatEnum
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.init_mixin import InitMixin
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class Freezable(InitMixin, ABC):
    """
    Derive a dataclass from this base to add the ability to freeze from further modifications of its fields.
    Once frozen, the instance cannot be unfrozen. This affects only the speed of setters but not of getters.

    Notes:
        - This base should be used for dataclass objects, use the appropriate base for each framework
        - Use tuple which is immutable instead of list when deriving from this class
    """

    _frozen: BuildWhatEnum | None = required(default=None, init=False, repr=False, compare=False)
    """Indicates what kind of instance has been frozen. Once frozen, the instance cannot be unfrozen."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        return bool(self._frozen)

    def what_frozen(self) -> BuildWhatEnum:
        """Return the parameter passed to the freeze method."""
        return self._frozen

    def freeze(self, *, what: BuildWhatEnum) -> None:
        """
        Freeze the instance without recursively calling freeze on its fields, which will be done by the build method.
        Once frozen, the instance cannot be unfrozen. The parameter indicates what kind of instance has been frozen.
        """
        if self._frozen:
            # Check that repeated freeze call has the same parameter
            if self._frozen != what:
                frozen_name = self._frozen.name if self._frozen else "None"
                what_name = what.name if what else "None"
                raise RuntimeError(f"Attempting to freeze as {self._frozen.name} when "
                                   f"the instance is already frozen as {what.name}.")
        elif what:
            # Freeze setting fields at root level
            object.__setattr__(self, "_frozen", what)
        else:
            raise RuntimeError("Parameter 'what' of freeze method is None.")

    def __setattr__(self, key, value):
        """Raise an error if invoked for a frozen instance.."""
        if getattr(self, "_frozen", None):
            raise AttributeError(f"Cannot modify field {TypeUtil.name(self)}.{key} because the instance is frozen.")
        object.__setattr__(self, key, value)
