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
from typing_extensions import Self
from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.clone_util import CloneUtil
from cl.runtime.records.protocols import TData
from cl.runtime.records.type_util import TypeUtil


class DataMixin:
    """Framework-neutral mixin adding 'build' and related methods to the class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @abstractmethod
    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""

    @abstractmethod
    def mark_frozen(self) -> Self:
        """
        Mark the instance as frozen without actually freezing it, which is the responsibility of build method.
        The action of marking the instance frozen cannot be reversed. Can be called more than once.
        """

    def check_frozen(self) -> None:
        """Raise an error if the instance is not frozen."""
        if not self.is_frozen():
            raise RuntimeError(f"{TypeUtil.name(self)} not frozen, invoke build method before first use.")

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

    def clone(self) -> Self:
        """Return an unfrozen object of the same type constructed from shallow copies of the public fields of self."""
        return CloneUtil.clone(self)

    def clone_as(self, result_type: type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields of self."""
        return CloneUtil.clone_as(self, result_type)
