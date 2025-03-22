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
from typing import Protocol
from typing import Tuple
from typing import Type
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID
from frozendict import frozendict
from typing_extensions import Self

PRIMITIVE_CLASSES = (str, float, bool, int, dt.date, dt.time, dt.datetime, UUID, bytes)
"""
The list of Python classes used to store primitive types, excludes those primitive types that do not have their own
Pyton classes such as long (uses Python class int) and timestamp (uses Python class UUID).
"""

PRIMITIVE_CLASS_NAMES = frozenset(type_.__name__ for type_ in PRIMITIVE_CLASSES)  # TODO: Rename
"""
The list of Python class names used to store primitive types, excludes those primitive types that do not have their own
Pyton classes such as long (uses Python type int) and timestamp (uses Python type UUID).
"""

PRIMITIVE_TYPE_NAMES = (
    "str",
    "float",
    "bool",
    "int",
    "long",  # Stored in int class
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

SEQUENCE_TYPE_NAMES = ("MutableSequence", "Sequence", "list", "tuple")
"""Names of classes that may be used to represent sequences, including abstract base classes."""

MAPPING_CLASSES = (dict, frozendict)
"""Classes that may be used to represent mapping, excluding abstract base classes."""

MAPPING_TYPE_NAMES = ("MutableMapping", "Mapping", "dict", "frozendict")
"""Names of classes that may be used to represent mapping, including abstract base classes."""


class DataProtocol(Protocol):
    """Protocol for a class that has slots and implements the builder pattern."""

    @classmethod
    def get_slots(cls) -> Tuple[str, ...]:
        """Get slot names for serialization without schema."""
        ...

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        ...

    def freeze(self) -> None:
        """
        Freeze the instance without recursively calling freeze on its fields, which will be done by the build method.
        Once frozen, the instance cannot be unfrozen. The parameter indicates what kind of instance has been frozen.
        """
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


class KeyProtocol(DataProtocol):
    """Protocol implemented by both keys and records."""

    @classmethod
    def get_key_type(cls) -> Type:
        """Return key type even when called from a record."""
        ...


class RecordProtocol(KeyProtocol):
    """Protocol implemented by records."""

    def get_key(self) -> KeyProtocol:
        """Return a new key object whose fields populated from self, do not return self."""
        ...


TPrimitive = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Type alias for Python classes used to store primitive values."""

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


def is_data(instance_or_type: Any) -> TypeGuard[DataProtocol]:
    """Fast partial check for DataProtocol, return True if the argument has 'freeze' method."""
    return hasattr(instance_or_type, "freeze")


def is_key(instance_or_type: Any) -> TypeGuard[KeyProtocol]:
    """
    Return True if the argument is a key but not a record based on the presence of 'get_key_type' method and the
    absence of 'get_key' method. Consider using a faster alternative 'is_key_or_record' if possible.
    """
    return hasattr(instance_or_type, "get_key_type") and not hasattr(instance_or_type, "get_key")


def is_key_or_record(instance_or_type: Any) -> TypeGuard[KeyProtocol]:
    """Return True if the argument is a key or record based on the presence of 'get_key_type' method."""
    return hasattr(instance_or_type, "get_key_type")


def is_record(instance_or_type: Any) -> TypeGuard[RecordProtocol]:
    """Return True if the argument is a record based on the presence of 'get_key' method."""
    return hasattr(instance_or_type, "get_key")


def is_singleton_key(instance_or_type: Any):  # TODO: Move elsewhere and review logic
    """Return True if the argument is a singleton key (has no key fields), error if not a key or has no slots."""
    if not is_key(instance_or_type):
        raise RuntimeError("Function 'is_singleton_key' is called on an object that is not a key.")
    if not hasattr(instance_or_type, "__slots__"):
        raise RuntimeError("Function 'is_singleton' is called on an object that has no __slots__ attribute.")
    return all(name.startswith("_") for name in instance_or_type.__slots__)
