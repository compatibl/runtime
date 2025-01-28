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
from typing import Literal
from typing import Protocol
from typing import Tuple
from typing import Type
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID
from typing_extensions import Self

_PRIMITIVE_TYPE_NAMES = {"str", "float", "bool", "int", "date", "time", "datetime", "UUID", "bytes"}

TPrimitive = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Supported primitive types for serialized data."""

TDataField = Dict[str, "TDataField"] | List["TDataField"] | TPrimitive | Enum
"""Supported field types for serialized data in dictionary format."""

TDataDict = Dict[str, TDataField]
"""Serialized data in dictionary format."""

TKeyField = Dict[str, "TKeyField"] | TPrimitive | Enum
"""Supported field types for serialized key in dictionary format."""

TKeyDict = Dict[str, TKeyField]
"""Serialized key in dictionary format."""

TQuery = Tuple[
    Type,  # Query type and its descendents will be returned by the query. It must include all query and order fields.
    Dict[str, Any],  # NoSQL query conditions in MongoDB format.
    Dict[str, Literal[1, -1]],  # NoSQL query order in MongoDB format.
]
"""NoSQL query data in MongoDB format."""

TObj = TypeVar("TObj")
"""Generic type parameter for any object."""

TRecord = TypeVar("TRecord")
"""Generic type parameter for a record."""

TKey = TypeVar("TKey")
"""Generic type parameter for a key."""

TEnum = TypeVar("TEnum", bound=Enum)
"""Generic type parameter for an enum."""


class BuildProtocol(Protocol):
    """Protocol for objects with build method."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes 'init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        ...


class FreezableProtocol(Protocol):
    """Protocol implemented by objects that require initialization."""

    def is_frozen(self) -> bool:
        """Return True if the instance has been frozen. Once frozen, the instance cannot be unfrozen."""
        ...

    def freeze(self) -> None:
        """
        Freeze the instance without recursively calling freeze on its fields, which will be done by the build method.
        Once frozen, the instance cannot be unfrozen. The parameter indicates what kind of instance has been frozen.
        """
        ...


class InitProtocol(Protocol):
    """Protocol implemented by objects that require initialization."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes 'init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        ...


class KeyProtocol(Protocol):
    """Protocol implemented by keys and also required for records which are derived from keys."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes 'init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        ...

    @classmethod
    def get_key_type(cls) -> Type:
        """Return key type even when called from a record."""
        ...


class RecordProtocol(Protocol):
    """Protocol implemented by records but not keys."""

    def build(self) -> Self:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes 'init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """
        ...

    # Do not use Protocol inheritance, repeat method instead as it is not yet supported by all static type checkers
    @classmethod
    def get_key_type(cls) -> Type:
        """Return key type even when called from a record."""
        ...

    def get_key(self) -> KeyProtocol:
        """Return a new key object whose fields populated from self, do not return self."""
        ...


def get_primitive_type_names() -> Tuple[str, ...]:
    """Returns the list of supported primitive type names."""
    return tuple(_PRIMITIVE_TYPE_NAMES)


def is_primitive(instance_or_type: Any) -> TypeGuard[TPrimitive]:
    """Returns true if one of the supported primitive types."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in _PRIMITIVE_TYPE_NAMES
    return result


def is_freezable(instance_or_type: Any) -> TypeGuard[FreezableProtocol]:
    """
    Return True if the instance is freezable (implements freeze).
    A class must not implement freeze unless all of its mutable elements also implement freeze.
    Among other things, this means a freezable class can have tuple elements but not list elements.
    """
    return hasattr(instance_or_type, "freeze")


def is_record(instance_or_type: Any) -> TypeGuard[RecordProtocol]:
    """Check if type or object is a record based on the presence of 'get_key' method."""
    return hasattr(instance_or_type, "get_key")


def is_record_or_key(instance_or_type: Any) -> TypeGuard[KeyProtocol]:
    """Check if type or object is a record or key based on the presence of 'get_key_type' method."""
    return hasattr(instance_or_type, "get_key_type")


def is_key(instance_or_type: Any) -> TypeGuard[KeyProtocol]:
    """
    Check if type or object is a key but not a record based on the presence of 'get_key_type' method and the
    absence of 'get_key' method. Consider using a faster alternative 'is_record_or_key' if possible.
    """
    return hasattr(instance_or_type, "get_key_type") and not hasattr(instance_or_type, "get_key")


def is_singleton_key(instance_or_type: Any):
    """Check if this is a singleton key (has no key fields), error if the object is not a key or has no slots."""
    if not is_key(instance_or_type):
        raise RuntimeError("Function 'is_singleton_key' is called on an object that is not a key.")
    if not hasattr(instance_or_type, "__slots__"):
        raise RuntimeError("Function 'is_singleton' is called on an object that has no __slots__ attribute.")
    return all(name.startswith("_") for name in instance_or_type.__slots__)


def has_init(instance_or_type: Any) -> TypeGuard[InitProtocol]:
    """Check if type or object requires initialization (InitProtocol) based on the presence of 'init' attribute."""
    return hasattr(instance_or_type, "init")
