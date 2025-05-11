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

import weakref
from abc import ABC
from typing_extensions import Self
from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.clone_util import CloneUtil
from cl.runtime.records.protocols import TData
from cl.runtime.records.type_util import TypeUtil

_FROZEN_IDS = set()
"""Global registry to track frozen status of Python object id's."""

_FROZEN_FINALIZERS = dict()
"""Adding a finalizer to this global dictionary prevents it from being collected before it is executed."""


class DataMixin(ABC):
    """Framework-neutral mixin adding 'build' and related methods to the class."""

    __slots__ = ("__weakref__",)
    """To prevent creation of __dict__ in derived types."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        return id(self) in _FROZEN_IDS

    def mark_frozen(self) -> Self:
        """
        Mark the instance as frozen without actually freezing it, which is the responsibility of build method.
        The action of marking the instance frozen cannot be reversed. Can be called more than once.
        """
        # Add Python object ID of self the global frozen ID registry
        _FROZEN_IDS.add(oid := id(self))
        # Register a finalizer to remove object ID from the registry when the object is finalized
        _FROZEN_FINALIZERS[oid] = weakref.finalize(self, _FROZEN_IDS.discard, oid)
        return self

    def check_frozen(self) -> None:
        """Raise an error if the instance is not frozen."""
        if not self.is_frozen():
            raise RuntimeError(f"{TypeUtil.name(self)} not frozen, invoke build method before first use.")

    def __setattr__(self, key, value):
        """Raise an error on attempt to modify a public field for a frozen instance."""
        if self.is_frozen() and not key.startswith("_"):
            type_name = TypeUtil.name(self)
            raise RuntimeError(f"Cannot modify public field {type_name}.{key} because the instance is frozen.")
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
