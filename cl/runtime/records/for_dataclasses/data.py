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

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True)
class Data(DataMixin, ABC):
    """
    Base for slotted classes other than keys or records based on dataclasses framework.
    Once frozen, the instance cannot be unfrozen. This affects only the speed of setters but not of getters.

    Notes:
        - This base should be used for dataclasses, use the appropriate import of Data for other frameworks
        - Use tuple which is immutable instead of list when deriving from this class
    """

    __frozen: bool = required(default=None, init=False, repr=False, compare=False)
    """True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        return bool(self.__frozen)

    def mark_frozen(self) -> Self:
        """
        Mark the instance as frozen without actually freezing it,which is the responsibility of build method.
        The action of marking the instance frozen cannot be reversed. Can be called more than once.
        """
        object.__setattr__(self, "_Data__frozen", True)
        return self
