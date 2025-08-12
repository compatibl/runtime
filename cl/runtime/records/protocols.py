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

import datetime as dt
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Mapping
from typing import Protocol
from typing import Sequence
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID
from bson import Int64
from frozendict import frozendict
from typing import Self

PRIMITIVE_CLASSES = (str, float, bool, int, Int64, dt.date, dt.time, dt.datetime, UUID, bytes)
"""The list of Python classes used to store primitive types, not the same as type names."""

PRIMITIVE_CLASS_NAMES = frozenset(type_.__name__ for type_ in PRIMITIVE_CLASSES)
"""The list of Python class names used to store primitive types, not the same as type names."""

PRIMITIVE_TYPE_NAMES = (
    "str",
    "float",
    "bool",
    "int",
    "long",  # Stored in int or Int64 class
    "date",
    "time",
    "datetime",
    "UUID",
    "timestamp",  # Stored in UUID class
    "bytes",
)
"""
The list of primitive type names, includes those primitive types that do not have their own
Pyton classes such as long (uses Python type int) and timestamp (uses Python type UUID).
"""

SEQUENCE_CLASSES = (list, tuple)
"""Classes that may be used to represent sequences, excluding abstract base classes."""

SEQUENCE_CLASS_NAMES = tuple(type_.__name__ for type_ in SEQUENCE_CLASSES)
"""Names of classes that may be used to represent sequences, excluding abstract base classes."""

SEQUENCE_TYPE_NAMES = ("MutableSequence", "Sequence", "list", "tuple")
"""Names of classes that may be used to represent sequences, including abstract base classes."""

MAPPING_CLASSES = (dict, frozendict)
"""Classes that may be used to represent mappings, excluding abstract base classes."""

MAPPING_CLASS_NAMES = tuple(type_.__name__ for type_ in MAPPING_CLASSES)
"""Names of classes that may be used to represent mappings, excluding abstract base classes."""

MAPPING_TYPE_NAMES = ("MutableMapping", "Mapping", "dict", "frozendict")
"""Names of classes that may be used to represent mappings, including abstract base classes."""

SEQUENCE_AND_MAPPING_CLASSES = tuple(x for x in (*SEQUENCE_CLASSES, *MAPPING_CLASSES))
"""Names of classes that may be used to represent mappings, excluding abstract base classes."""

SEQUENCE_AND_MAPPING_CLASS_NAMES = tuple(x for x in (*SEQUENCE_CLASS_NAMES, *MAPPING_CLASS_NAMES))
"""Names of classes that may be used to represent mappings, excluding abstract base classes."""

SEQUENCE_AND_MAPPING_TYPE_NAMES = tuple(x for x in (*SEQUENCE_TYPE_NAMES, *MAPPING_TYPE_NAMES))
"""Names of classes that may be used to represent mappings, excluding abstract base classes."""

TObj = TypeVar("TObj")
"""Generic type parameter for any object."""

class BuilderProtocol(Protocol):
    """Protocol for freezable fields and builder pattern support."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        ...

    def mark_frozen(self) -> Self:
        """
        Mark the instance as frozen without actually freezing it, which is the responsibility of build method.
        The action of marking the instance frozen cannot be reversed. Can be called more than once.
        """
        ...

    def check_frozen(self) -> None:
        """Raise an error if the instance is not frozen."""
        ...

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        ...

    def cast(self, cast_to: type[TObj]) -> TObj:
        """
        Cast self to type cast_to after checking it is an instance of cast_to, error message otherwise.
        This provides a runtime-checked alternative to typing.cast which does not check anything at runtime.
        """
        ...

class DataProtocol(BuilderProtocol):
    """Protocol for a class that has slots and implements the builder pattern."""

    @classmethod
    def get_slots(cls) -> tuple[str, ...]:
        """Return slots the order of declaration from base to derived."""
        ...

    def clone(self) -> Self:
        """Return an unfrozen object of the same type populated by shallow copies of public fields."""
        ...

    def clone_as(self, result_type: type[TObj]) -> TObj:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields."""
        ...


class KeyProtocol(DataProtocol):
    """Protocol implemented by both keys and records."""

    @classmethod
    def get_key_type(cls) -> type:
        """Return key type even when called from a record."""
        ...


class RecordProtocol(KeyProtocol):
    """Protocol implemented by records."""

    def get_key(self) -> KeyProtocol:
        """Return a new key object whose fields populated from self, do not return self."""
        ...


TPrimitive = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Type alias for Python classes used to store primitive values."""

TSequence = list | tuple | Sequence
"""Type alias for a supported sequence type."""

TMapping = dict | frozendict | Mapping
"""Type alias for a supported mapping type."""

TDataField = Dict[str, "TDataField"] | List["TDataField"] | TPrimitive | Enum
"""Field types for serialized data in dictionary format."""

TDataDict = Dict[str, TDataField]
"""Serialized data in dictionary format."""

TKeyField = Dict[str, "TKeyField"] | TPrimitive | Enum
"""Field types for serialized key in dictionary format."""

TKeyDict = Dict[str, TKeyField]
"""Serialized key in dictionary format."""

TObj = TypeVar("TObj")
"""Generic type parameter for any object."""

TEnum = TypeVar("TEnum", bound=Enum)
"""Generic type parameter for an enum."""

TData = TypeVar("TData", bound=DataProtocol)
"""Generic type parameter for a class that has slots and implements the builder pattern."""

TKey = TypeVar("TKey", bound=KeyProtocol)
"""Generic type parameter for a key."""

TRecord = TypeVar("TRecord", bound=RecordProtocol)
"""Generic type parameter for a record."""


def is_primitive(instance_or_type: Any) -> TypeGuard[TPrimitive]:
    """Returns true if the argument is one of the supported primitive classes."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in PRIMITIVE_CLASS_NAMES
    return result


def is_enum(instance_or_type: Any) -> TypeGuard[TEnum]:
    """
    Returns true if the argument is an enum.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)

    # Ensure the argument is not one of the base enum classes such as Enum, IntEnum, etc.
    not_base_enum = type_.__module__ != "enum"

    # Derived from Enum but not one of the base enum classes
    return issubclass(type_, Enum) and not type_.__name__.startswith("_") and not_base_enum


def is_sequence(instance_or_type: Any) -> TypeGuard[TSequence]:
    """Returns true if the argument is one of the supported sequence types."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in SEQUENCE_TYPE_NAMES
    return result


def is_mapping(instance_or_type: Any) -> TypeGuard[TSequence]:
    """Returns true if the argument is one of the supported mapping types."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in MAPPING_TYPE_NAMES
    return result


def is_abstract(instance_or_type: Any) -> bool:
    """True if the argument is an abstract class."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return bool(getattr(type_, "__abstractmethods__", None))


def is_builder(instance_or_type: Any) -> TypeGuard[TData]:
    """
    True if the argument has 'build' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "build") and not type_.__name__.startswith("_")


def is_data_key_or_record(instance_or_type: Any) -> TypeGuard[TData]:
    """
    True if the argument has 'get_slots' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_slots") and not type_.__name__.startswith("_")


def is_key_or_record(instance_or_type: Any) -> TypeGuard[TKey]:
    """
    True if the argument has 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_key_type") and not type_.__name__.startswith("_")


def is_data(instance_or_type: Any) -> TypeGuard[TKey]:
    """
    True if the argument has 'get_slots' method but not 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_slots") and not hasattr(type_, "get_key_type") and not type_.__name__.startswith("_")


def is_key(instance_or_type: Any) -> TypeGuard[TKey]:
    """
    True if the argument has 'get_key_type' method but not 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_key_type") and not hasattr(type_, "get_key") and not type_.__name__.startswith("_")


def is_record(instance_or_type: Any) -> TypeGuard[TRecord]:
    """
    Return True if the argument has 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_key") and not type_.__name__.startswith("_")


def is_singleton_key(instance_or_type: Any):  # TODO: Move elsewhere and review logic
    """Return True if the argument is a singleton key (has no key fields), error if not a key or has no slots."""
    if not is_key(instance_or_type):
        raise RuntimeError("Function 'is_singleton_key' is called on an object that is not a key.")
    if not hasattr(instance_or_type, "__slots__"):
        raise RuntimeError("Function 'is_singleton' is called on an object that has no __slots__ attribute.")
    return all(name.startswith("_") for name in instance_or_type.get_slots())
