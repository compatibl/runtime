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

from typing_extensions import Self
from cl.runtime.records.clone_util import CloneUtil
from cl.runtime.records.protocols import TData


class FrozenDataMixin:
    """
    Framework-neutral mixin for classes that are frozen on construction, intended
    for lightweight classes that do not require validation against the schema.
    """

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    def is_frozen(cls) -> bool:
        """Frozen on construction, always true."""
        return True

    @classmethod
    def mark_frozen(cls) -> None:
        """Frozen on construction, do nothing."""

    def check_frozen(self) -> None:
        """Frozen on construction, do nothing."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        Note - validation against the schema is not performed for this class.
        """
        # Invoke '__init' in the order from base to derived
        # Keep track of which init methods in class hierarchy were already called
        invoked = set()
        # Reverse the MRO to start from base to derived
        for class_ in reversed(self.__class__.__mro__):
            # Remove leading underscores from the class name when generating mangling for __init
            # to support classes that start from _ to mark them as protected
            class_init = getattr(class_, f"_{class_.__name__.lstrip('_')}__init", None)
            if class_init is not None and (qualname := class_init.__qualname__) not in invoked:
                # Add qualname to invoked to prevent executing the same method twice
                invoked.add(qualname)
                # Invoke '__init' method if it exists, otherwise do nothing
                class_init(self)
        return self

    def clone_as(self, result_type: type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields of self."""
        return CloneUtil.clone_as(self, result_type)
