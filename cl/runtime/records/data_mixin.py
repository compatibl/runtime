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
from abc import abstractmethod
from enum import Enum
from typing import Self
from typing import TypeVar
from cl.runtime.records.builder_mixin import BuilderMixin
from cl.runtime.records.data_util import DataUtil
from cl.runtime.records.protocols import PrimitiveTypes
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import is_mixin_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_spec import TypeSpec


class DataMixin(BuilderMixin, ABC):
    """Framework-neutral mixin adding 'build' and related methods to the class."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    def get_field_names(cls) -> tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""

    @classmethod
    @abstractmethod
    def get_type_spec(cls) -> TypeSpec:
        """Return type specification for this class."""
        if is_mixin_type(cls):
            # Return data spec with no fields if a mixin class
            return DataSpec(
                type_=cls,
                fields=[],
            ).build()
        else:
            # Otherwise derived type must implement
            raise RuntimeError(
                f"{typename(cls)} is not a mixin and must override DataMixin.get_type_spec method\n"
                f"to provide information about its fields."
            )

    def build(self) -> Self:
        """
        The implementation of the build method in DataMixin performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Validates root level object against the schema and calls its 'mark_frozen' method
        """
        return DataUtil.build_(self, TypeHint.for_type(type(self)))

    def clone(self) -> Self:
        """Return an unfrozen object of the same type populated by shallow copies of public fields."""
        return self.clone_as(type(self))

    def clone_as(self, result_type: type[TObj]) -> TObj:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields."""
        return result_type(**{k: getattr(self, k) for k in self.get_field_names()})


TDataField = dict[str, "TDataField"] | list["TDataField"] | PrimitiveTypes | Enum  # TODO: Review potential replacement by a non-generic hint
"""Field types for serialized data in dictionary format."""

TDataDict = dict[str, TDataField]  # TODO: Review potential replacement by a non-generic hint
"""Serialized data in dictionary format."""

TData = TypeVar("TData", bound=DataMixin)  # TODO: Review potential replacement by a non-generic hint
"""Generic type parameter for a class that has slots and implements the builder pattern."""
