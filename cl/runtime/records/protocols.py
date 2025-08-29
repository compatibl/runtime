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
from typing import Mapping
from typing import Protocol
from typing import Self
from typing import Sequence
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID
from bson import Int64
from frozendict import frozendict

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

CONDITION_CLASS_NAMES = (
    "And",
    "Exists",
    "Gt",
    "Gte",
    "In",
    "Lt",
    "Lte",
    "Not",
    "NotIn",
    "Or",
    "Range",
)
"""
The list of condition class names."""

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

TPrimitive = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Type alias for Python classes used to store primitive values."""

TSequence = list | tuple | Sequence
"""Type alias for a supported sequence type."""

TMapping = dict | frozendict | Mapping
"""Type alias for a supported mapping type."""

TEnum = TypeVar("TEnum", bound=Enum)
"""Generic type parameter for an enum."""


def is_empty(
    data: Any,
) -> bool:  # TODO: Review if we should consider empty sequences as None during build or serialization
    """Returns true if the argument is None or an empty string, sequence or mapping."""
    return data in (None, "") or (data.__class__.__name__ in SEQUENCE_AND_MAPPING_CLASS_NAMES and len(data) == 0)


def is_primitive(instance_or_type: Any) -> TypeGuard[TPrimitive]:
    """Returns true if the argument is one of the supported primitive classes."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in PRIMITIVE_CLASS_NAMES
    return result


def is_condition(instance_or_type: Any) -> TypeGuard[Any]:  # TODO: Add protocol
    """Returns true if the argument is one of the supported condition classes."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    result = type_.__name__ in CONDITION_CLASS_NAMES
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


def is_mixin(instance_or_type: Any) -> bool:
    """True if the argument is a mixin class, detect base on Mixin name suffix only."""
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return type_.__name__.endswith("Mixin")


def is_builder(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[BuilderMixin]]:
    """
    True if the argument has 'build' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "build") and not type_.__name__.startswith("_")


def is_data_key_or_record(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[DataMixin]]:
    """
    True if the argument has 'get_field_names' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_field_names") and not type_.__name__.startswith("_")


def is_key_or_record(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[KeyMixin]]:
    """
    True if the argument has 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_key_type") and not type_.__name__.startswith("_")


def is_data(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[DataMixin]]:
    """
    True if the argument has 'get_field_names' method but not 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return (
        hasattr(type_, "get_field_names") and not hasattr(type_, "get_key_type") and not type_.__name__.startswith("_")
    )


def is_key(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[KeyMixin]]:
    """
    True if the argument has 'get_key_type' method but not 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
    return hasattr(type_, "get_key_type") and not hasattr(type_, "get_key") and not type_.__name__.startswith("_")


def is_record(instance_or_type: Any) -> bool:  # TODO: !!! TypeGuard[type[RecordMixin]]:
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
    return all(name.startswith("_") for name in instance_or_type.get_field_names())
