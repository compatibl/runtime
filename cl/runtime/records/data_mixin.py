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

from abc import abstractmethod
from typing import Tuple
from typing import Type
from typing_extensions import Self
from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.protocols import TData


class DataMixin:
    """Mixin adding 'build' method to the class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    @abstractmethod
    def get_slots(cls) -> Tuple[str, ...]:
        """Get slot names for serialization without schema."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        return BuildUtil.build(self)

    def clone(self: Self) -> Self:
        """Return an unfrozen object of the same type populated by shallow copies of public fields."""
        result = type(self)()
        slots = self.get_slots()
        for attr in slots:
            if not attr.startswith("_"):  # Skip private fields
                setattr(result, attr, getattr(self, attr))
        return result

    def clone_as(self: Self, result_type: Type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields."""
        result = result_type()
        slots = self.get_slots()
        for attr in slots:
            if not attr.startswith("_"):  # Skip private fields
                setattr(result, attr, getattr(self, attr))
        return result
