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
from typing import Any, MutableSequence, MutableMapping
from typing import Mapping
from typing import Sequence
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID
from bson import Int64
from frozendict import frozendict

PRIMITIVE_TYPES = (str, float, bool, int, Int64, dt.date, dt.time, dt.datetime, UUID, bytes, type)
"""The list of Python classes used to store primitive types, not the same as type names."""

PRIMITIVE_TYPE_NAMES = frozenset(type_.__name__ for type_ in PRIMITIVE_TYPES)
"""The list of Python class names used to store primitive types, not the same as type names."""

CONDITION_TYPE_NAMES = (
    "And",
    "Condition",  # Abstract base
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
"""Names of types that may be used to represent conditions, including abstract base classes."""

SEQUENCE_TYPES = (list, tuple)
"""Types that may be used to represent sequences, excluding abstract base classes."""

SEQUENCE_TYPE_NAMES = ("MutableSequence", "Sequence", "list", "tuple")
"""Names of types that may be used to represent sequences, including abstract base classes."""

MAPPING_TYPES = (dict, frozendict)
"""Types that may be used to represent mappings, excluding abstract base classes."""

MAPPING_TYPE_NAMES = ("MutableMapping", "Mapping", "dict", "frozendict")
"""Names of types that may be used to represent mappings, including abstract base classes."""

PrimitiveTypes = str | float | bool | int | dt.date | dt.time | dt.datetime | UUID | bytes
"""Type alias for Python classes used to store primitive values."""

SequenceTypes = list | tuple | Sequence | MutableSequence
"""Type alias for a supported sequence type."""

MappingTypes = dict | frozendict | Mapping | MutableMapping
"""Type alias for a supported mapping type."""

TObj = TypeVar("TObj")
"""Generic type parameter for any object."""

TEnum = TypeVar("TEnum", bound=Enum)
"""Generic type parameter for an enum."""


def is_empty(
    data: Any,
) -> bool:
    """True if the argument is None or an empty primitive type, False for an empty sequence or mapping."""
    return data in (None, "")


def is_primitive_type(type_: type) -> TypeGuard[type[PrimitiveTypes]]:
    """Returns true if the argument is one of the supported primitive types."""
    if isinstance(type_, type):
        # Use class names to avoid import discrepancies for UUID
        # Use issubclass(type_, type) to include ABCMeta and other metaclasses of type
        return type_.__name__ in PRIMITIVE_TYPE_NAMES or issubclass(type_, type)
    else:
        raise RuntimeError(f"The argument of is_primitive is an instance of {type(type_).__name__} rather than type.")


def is_enum_type(type_: type) -> TypeGuard[type[Enum]]:
    """Derived from Enum but not one of the base enum classes and the name does not start from underscore."""
    if isinstance(type_, type):
        return issubclass(type_, Enum) and type_.__module__ != "enum" and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(f"The argument of is_enum is an instance of {type(type_).__name__} rather than type.")


def is_sequence_type(type_: type) -> TypeGuard[SequenceTypes]:
    """Returns true if the argument is one of the supported sequence types."""
    if isinstance(type_, type):
        return type_.__name__ in SEQUENCE_TYPE_NAMES
    else:
        raise RuntimeError(f"The argument of is_sequence is an instance of {type(type_).__name__} rather than type.")


def is_mapping_type(type_: type) -> TypeGuard[MappingTypes]:
    """Returns true if the argument is one of the supported mapping types."""
    if isinstance(type_, type):
        return type_.__name__ in MAPPING_TYPE_NAMES
    else:
        raise RuntimeError(f"The argument of is_mapping is an instance of {type(type_).__name__} rather than type.")


def is_abstract_type(type_: type) -> bool:
    """True if the argument is an abstract class."""
    if isinstance(type_, type):
        return bool(getattr(type_, "__abstractmethods__", None))
    else:
        raise RuntimeError(f"The argument of is_abstract is an instance of {type(type_).__name__} rather than type.")


def is_builder_type(type_: type) -> bool:
    """
    True if the argument has 'build' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return hasattr(type_, "build") and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(f"The argument of is_builder is an instance of {type(type_).__name__} rather than type.")


def is_data_key_or_record_type(type_: type) -> bool:
    """
    True if the argument has 'get_field_names' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return hasattr(type_, "get_field_names") and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_data_key_or_record is an instance of {type(type_).__name__} rather than type."
        )


def is_key_or_record_type(type_: type) -> bool:
    """
    True if the argument has 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return hasattr(type_, "get_key_type") and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_key_or_record is an instance of {type(type_).__name__} rather than type."
        )


def is_data_type(type_: type) -> bool:
    """
    True if the argument has 'get_field_names' method but not 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return (
            hasattr(type_, "get_field_names")
            and not hasattr(type_, "get_key_type")
            and not type_.__name__.startswith("_")
        )
    else:
        raise RuntimeError(f"The argument of is_data is an instance of {type(type_).__name__} rather than type.")


def is_key_type(type_: type) -> bool:
    """
    True if the argument has 'get_key_type' method but not 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return hasattr(type_, "get_key_type") and not hasattr(type_, "get_key") and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(f"The argument of is_key is an instance of {type(type_).__name__} rather than type.")


def is_record_type(type_: type) -> bool:
    """
    Return True if the argument has 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    if isinstance(type_, type):
        return hasattr(type_, "get_key") and not type_.__name__.startswith("_")
    else:
        raise RuntimeError(f"The argument of is_record is an instance of {type(type_).__name__} rather than type.")


def is_condition_type(type_: type) -> bool:
    """Returns true if the argument is one of the supported condition types."""
    if isinstance(type_, type):
        # Use class names to avoid a cyclic reference
        return type_.__name__ in CONDITION_TYPE_NAMES
    else:
        raise RuntimeError(f"The argument of is_enum is an instance of {type(type_).__name__} rather than type.")
