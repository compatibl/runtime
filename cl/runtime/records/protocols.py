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
from typing import Any, get_origin
from typing import Mapping
from typing import MutableMapping
from typing import MutableSequence
from typing import Sequence
from typing import TypeGuard
from typing import TypeVar
from uuid import UUID

import numpy as np
from bson import Int64
from frozendict import frozendict
from cl.runtime.records.typename import typename

PRIMITIVE_TYPES = (
    str,
    float,
    np.float64,
    bool,
    int,
    Int64,
    dt.date,
    dt.time,
    dt.datetime,
    UUID,
    bytes,
    type,
)
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

NDARRAY_TYPE_NAMES = ("ndarray", "NDArray")
"""Names of types or generic aliases used for ndarray variables or generic aliases."""

PrimitiveTypes = str | float | np.float64 | bool | int | Int64 | dt.date | dt.time | dt.datetime | UUID | bytes | type  # TODO: Rename to PrimitiveType?
"""Type alias for Python classes used to store primitive values."""

SequenceTypes = list | tuple | Sequence | MutableSequence  # TODO: Replace by Sequence or MutableSequence?
"""Type alias for a supported sequence type."""

MappingTypes = dict | frozendict | Mapping | MutableMapping  # TODO: Replace by Mapping or MutableMapping?
"""Type alias for a supported mapping type."""

FloatVector = np.ndarray[tuple[int], np.dtype[np.float64]]
"""One-dimensional NumPy array with dtype=np.float64."""

FloatMatrix = np.ndarray[tuple[int, int], np.dtype[np.float64]]
"""Two-dimensional numpy array with dtype=np.float64."""

FloatCube = np.ndarray[tuple[int, int, int], np.dtype[np.float64]]
"""Three-dimensional numpy array with dtype=np.float64, sizes are not necessarily the same (not a literal cube)."""

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
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        # Use class names to avoid import discrepancies for UUID
        # Use issubclass(type_, type) to include ABCMeta and other metaclasses of type
        # Use type_name == "dtype" to include numpy dtype generics
        return type_name in PRIMITIVE_TYPE_NAMES or type_name == "dtype" or issubclass(type_, type)
    else:
        raise RuntimeError(
            f"The argument of is_primitive_type is an instance of type {type(type_).__name__}\n"
            f"rather than type variable for this type, use type(arg) instead of arg."
        )


def is_enum_type(type_: type) -> TypeGuard[type[Enum]]:
    """Derived from Enum but not one of the base enum classes and the name does not start from underscore."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return issubclass(type_, Enum) and type_.__module__ != "enum" and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_enum_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_sequence_type(type_: type) -> TypeGuard[type[SequenceTypes]]:
    """Returns true if the argument is one of the supported sequence types."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return type_name in SEQUENCE_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_sequence_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_mapping_type(type_: type) -> TypeGuard[type[MappingTypes]]:
    """Returns true if the argument is one of the supported mapping types."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return type_name in MAPPING_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_mapping_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_ndarray_type(type_: type) -> TypeGuard[type[np.ndarray]]:
    """Returns true if the argument is ndarray or one of its supported generic aliases."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        # Condition will match np.ndarray or generic alias for ndarray (including, currently, for NDArray)
        return type_name in NDARRAY_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_ndarray_type is an instance of type {type(type_).__name__}\nrather than type variable for this type or a generic alias,\nuse type(arg) instead of arg."
        )


def is_abstract_type(type_: type) -> bool:
    """True if the argument is an abstract class."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return bool(getattr(type_, "__abstractmethods__", None))
    else:
        raise RuntimeError(
            f"The argument of is_abstract_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_mixin_type(type_: type) -> bool:
    """True if the argument is a mixin class (class without instance fields), detected by classname suffix."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return typename(type_).endswith("Mixin")
    else:
        raise RuntimeError(
            f"The argument of is_mixin_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_builder_type(type_: type) -> bool:
    """
    True if the argument has 'build' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return hasattr(type_, "build") and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_builder_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_data_key_or_record_type(type_: type) -> bool:
    """
    True if the argument has 'get_field_names' method (includes data, keys and records), may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return hasattr(type_, "get_field_names") and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_data_key_or_record_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_key_or_record_type(type_: type) -> bool:
    """
    True if the argument has 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return hasattr(type_, "get_key_type") and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_key_or_record_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_data_type(type_: type) -> bool:
    """
    True if the argument has 'get_field_names' method but not 'get_key_type' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return (
            hasattr(type_, "get_field_names")
            and not hasattr(type_, "get_key_type")
            and not type_name.startswith("_")
        )
    else:
        raise RuntimeError(
            f"The argument of is_data_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_key_type(type_: type) -> bool:
    """
    True if the argument has 'get_key_type' method but not 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return hasattr(type_, "get_key_type") and not hasattr(type_, "get_key") and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_key_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_record_type(type_: type) -> bool:
    """
    Return True if the argument has 'get_key' method, may be abstract or a mixin.
    Excludes classes whose name starts from underscore.
    """
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return hasattr(type_, "get_key") and not type_name.startswith("_")
    else:
        raise RuntimeError(
            f"The argument of is_record_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )


def is_condition_type(type_: type) -> bool:
    """Returns true if the argument is one of the supported condition types."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        # Use class names to avoid a cyclic reference
        return type_name in CONDITION_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_condition_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )
