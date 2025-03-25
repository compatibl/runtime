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
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.slots_util import SlotsUtil


class DataMixin:
    """Mixin adding 'build' method to the class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @abstractmethod
    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""

    @abstractmethod
    def mark_frozen(self) -> None:
        """
        Mark the instance as frozen without actually freezing it,which is the responsibility of build method.
        The action of marking the instance frozen cannot be reversed.
        """

    def __setattr__(self, key, value):
        """Raise an error on attempt to modify a public field for a frozen instance."""
        if getattr(self, "_Data__frozen", False) and not key.startswith("_"):
            raise RuntimeError(
                f"Cannot modify public field {TypeUtil.name(self)}.{key} " f"because the instance is frozen."
            )
        object.__setattr__(self, key, value)

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Validates root level object against the schema and calls its 'mark_frozen' method
        """
        return BuildUtil.typed_build(self)

    def clone(self: Self) -> Self:
        """Return an unfrozen object of the same type populated by shallow copies of public fields."""
        type_ = type(self) # TODO: Consider using constructor with fields
        result = type_()
        slots = SlotsUtil.get_slots(type_)
        for attr in slots:
            if not attr.startswith("_"):  # Skip private fields
                setattr(result, attr, getattr(self, attr))
        return result

    def clone_as(self: Self, result_type: Type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields."""
        result = result_type()  # TODO: Consider using constructor with fields
        slots = SlotsUtil.get_slots(type(self))
        for attr in slots:
            if not attr.startswith("_"):  # Skip private fields
                setattr(result, attr, getattr(self, attr))
        return result
