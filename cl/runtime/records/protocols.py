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

import collections
import datetime as dt
from enum import Enum
from inspect import isabstract
from types import GenericAlias
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
from numpy._typing import NDArray

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

PREDICATE_TYPE_NAMES = (
    "Predicate",  # Abstract base
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
"""Names of types that may be used to represent predicates, including abstract base classes."""

SEQUENCE_TYPES = (list, tuple, MutableSequence, Sequence, collections.abc.MutableSequence, collections.abc.Sequence)
"""Types that may be used to represent sequences, excluding abstract base classes."""

SEQUENCE_TYPE_NAMES = ("list", "tuple", "MutableSequence", "Sequence")
"""Names of types that may be used to represent sequences, including abstract base classes."""

MAPPING_TYPES = (dict, frozendict, MutableMapping, Mapping, collections.abc.MutableMapping, collections.abc.Mapping)
"""Types that may be used to represent mappings, excluding abstract base classes."""

MAPPING_TYPE_NAMES = ("dict", "frozendict", "MutableMapping", "Mapping")
"""Names of types that may be used to represent mappings, including abstract base classes."""

NDARRAY_TYPES = (np.ndarray, NDArray)
"""Types used for ndarray variables."""

NDARRAY_TYPE_NAMES = ("ndarray", "NDArray")
"""Names of types or generic aliases used for ndarray variables or generic aliases."""

CONTAINER_TYPES = (*SEQUENCE_TYPES, *MAPPING_TYPES, *NDARRAY_TYPES)
"""All supported container types."""

CONTAINER_TYPE_NAMES = (*SEQUENCE_TYPE_NAMES, *MAPPING_TYPE_NAMES, *NDARRAY_TYPE_NAMES)
"""All supported container type names."""

PrimitiveTypes = (
    str | float | np.float64 | bool | int | Int64 | dt.date | dt.time | dt.datetime | UUID | bytes | type
)  # TODO: Rename to PrimitiveType?
"""Type alias for Python classes used to store primitive values."""

SequenceTypes = list | tuple | Sequence | MutableSequence | collections.abc.MutableSequence | collections.abc.Sequence
"""Type alias for a supported sequence type."""

MappingTypes = dict | frozendict | MutableMapping | Mapping | collections.abc.MutableMapping | collections.abc.Mapping
"""Type alias for a supported mapping type."""

FloatArray = np.ndarray[Any, np.dtype[np.float64]]
"""NumPy array with dtype=np.float64 and any number of dimensions."""

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
    # Do not use 'in' because data may be a sequence or mapping
    return data is None or (isinstance(data, (str, bytes)) and len(data) == 0)


def is_type(type_: type) -> TypeGuard[type | GenericAlias]:
    """Returns true if the argument is a genuine type or a supported container."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if type_ is not None:
        # Recursively call is_type on origin until it is None
        return (
                isinstance(type_, type) or
                ((type_name := getattr(type_, "__name__", None)) is not None and type_name in CONTAINER_TYPE_NAMES) or
                is_type(get_origin(type_))
        )
    else:
        # Original argument is None or no longer a generic alias and origin is None
        return False


def is_primitive_type(type_: type) -> TypeGuard[type[PrimitiveTypes]]:
    """Returns true if the argument is one of the supported primitive types."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        # Use class names to avoid import discrepancies for UUID
        # Use type_name == "dtype" to include numpy dtype generics
        # Use isinstance(type_, type) to guard issubclass() against unsupported GenericAlias classes.
        # Use issubclass(type_, type) to include ABCMeta and other metaclasses of type.
        return (
            type_name in PRIMITIVE_TYPE_NAMES
            or type_name == "dtype"
            or (isinstance(type_, type) and issubclass(type_, type))
        )
    else:
        raise RuntimeError(
            f"The argument of is_primitive_type is an instance of type {type(type_).__name__}\n"
            f"rather than type variable for this type, use type(arg) instead of arg."
        )


def is_enum_type(type_: type) -> TypeGuard[type[Enum]]:
    """Derived from Enum but not one of the base enum classes and the name does not start from underscore."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    # Use isinstance(type_, type) to guard issubclass() against GenericAlias classes.
    # Use issubclass(type_, Enum) to check if derived from Enum.
    # Use type_.__module__ != "enum" to exclude base enum classes.
    # Use not type_name.startswith("_") to exclude private enum classes.
    if (type_name := getattr(type_, "__name__", None)) is not None:
        return (
            isinstance(type_, type)
            and issubclass(type_, Enum)
            and type_.__module__ != "enum"
            and not type_name.startswith("_")
        )
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
        # Will match np.ndarray or generic alias for ndarray (including, currently, for NDArray)
        return type_name in NDARRAY_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_ndarray_type is an instance of type {type(type_).__name__}\nrather than type variable for this type or a generic alias,\nuse type(arg) instead of arg."
        )


def is_abstract_type(type_: type) -> bool:
    """True if the argument is an abstract class."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    return isabstract(type_)


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
            hasattr(type_, "get_field_names") and not hasattr(type_, "get_key_type") and not type_name.startswith("_")
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


def is_predicate_type(type_: type) -> bool:
    """Returns true if the argument is one of the supported query predicate types."""
    # Do not use isinstance(type_, type) to accept GenericAlias classes, including from packages (e.g., numpy)
    if (type_name := getattr(type_, "__name__", None)) is not None:
        # Use class names to avoid a cyclic reference
        return type_name in PREDICATE_TYPE_NAMES
    else:
        raise RuntimeError(
            f"The argument of is_predicate_type is an instance of type {type(type_).__name__}\nrather than type variable for this type, use type(arg) instead of arg."
        )
