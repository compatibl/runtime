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
from typing import runtime_checkable
from uuid import UUID

from typing_extensions import Self

_PRIMITIVE_TYPE_NAMES = {"str", "float", "bool", "int", "date", "time", "datetime", "UUID", "bytes"}

PrimitiveType = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Supported primitive value types excluding None."""

TPrimitive = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes | None  # TODO: Deprecated
"""Supported primitive value types for serialized data in dictionary format."""

TDataField = Dict[str, "TDataField"] | List["TDataField"] | TPrimitive | Enum | None
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


class InitProtocol(Protocol):
    """Protocol implemented by objects that require initialization."""

    def init_all(self) -> Self:
        """
        Invoke 'init' for each class in the order from base to derived, freeze if freezable, then validate the schema.
        Return self to enable method chaining.
        """
        ...


@runtime_checkable
class KeyProtocol(Protocol):
    """Protocol implemented by keys and also required for records which are derived from keys."""

    # Do not use Protocol inheritance, repeat method instead as it is not yet supported by all static type checkers
    def init_all(self) -> Self:
        """
        Invoke 'init' for each class in the order from base to derived, freeze if freezable, then validate the schema.
        Return self to enable method chaining.
        """
        ...

    @classmethod
    def get_key_type(cls) -> Type:
        """Return key type even when called from a record."""
        ...


class RecordProtocol(Protocol):
    """Protocol implemented by records but not keys."""

    # Do not use Protocol inheritance, repeat method instead as it is not yet supported by all static type checkers
    def init_all(self) -> Self:
        """
        Invoke 'init' for each class in the order from base to derived, freeze if freezable, then validate the schema.
        Return self to enable method chaining.
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


def is_primitive(instance_or_type: Any) -> TypeGuard[PrimitiveType]:
    """Returns true if one of the supported primitive types."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in _PRIMITIVE_TYPE_NAMES
    return result


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


def has_init(instance_or_type: Any) -> TypeGuard[InitProtocol]:
    """Check if type or object requires initialization (InitProtocol) based on the presence of 'init' attribute."""
    return hasattr(instance_or_type, "init")
