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

from dataclasses import MISSING
from dataclasses import fields
from dataclasses import is_dataclass
from enum import Enum
from types import NoneType
from types import UnionType
from typing import Any
from typing import TypeVar
from typing import Union
from typing import get_args
from typing import get_origin
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.protocols import _PRIMITIVE_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil

T = TypeVar("T")


class BuildUtil:
    """Helper class for BuildMixin."""

    @classmethod
    def build(cls, obj: T) -> T:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (1) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (2) Invokes 'freeze' method of this class
        Returns self to enable method chaining.
        """

        if (slots := getattr(obj, "__slots__", None)) is not None:
            # Has slots, process as data, key or record
            if obj.is_frozen():
                # Stop further processing and return if the object has been frozen to
                # prevent repeat initialization of shared instances
                return obj

            # Invoke '__init' in the order from base to derived
            # Keep track of which init methods in class hierarchy were already called
            invoked = set()
            # Reverse the MRO to start from base to derived
            for class_ in reversed(obj.__class__.__mro__):
                # Remove leading underscores from the class name when generating mangling for __init
                class_init = getattr(class_, f"_{class_.__name__.lstrip('_')}__init", None)
                if class_init is not None and (qualname := class_init.__qualname__) not in invoked:
                    # Add qualname to invoked to prevent executing the same method twice
                    invoked.add(qualname)
                    # Invoke '__init' method if it exists, otherwise do nothing
                    class_init(obj)

            # Recursively call 'build' on public fields except those that are None, primitive or Enum
            # and assign the result of build back to the field
            tuple(
                setattr(obj, slot, cls.build(x))
                for slot in slots
                if not slot.startswith("_")
                and (x := getattr(obj, slot, None)) is not None
                and type(x).__name__ not in _PRIMITIVE_TYPE_NAMES
                and not isinstance(x, Enum)
            )

            # After the init methods, call freeze method if implemented, continue without error if not
            obj.freeze()

            # Perform validation against the schema after the object is frozen and return
            cls.validate(obj)
            return obj
        elif isinstance(obj, list):
            # Recursively invoke on tuple elements in-place, skip primitive types or enums
            return [
                (
                    cls.build(v)
                    if v is not None and type(v).__name__ not in _PRIMITIVE_TYPE_NAMES and not isinstance(v, Enum)
                    else v
                )
                for v in obj
            ]
        elif isinstance(obj, tuple):
            # Recursively invoke on tuple elements in-place, skip primitive types or enums
            return tuple(
                (
                    cls.build(v)
                    if v is not None and type(v).__name__ not in _PRIMITIVE_TYPE_NAMES and not isinstance(v, Enum)
                    else v
                )
                for v in obj
            )
        elif isinstance(obj, dict):  # TODO: Switch to frozendict and Map
            # Recursively invoke on dict elements in-place, skip primitive types or enums
            return dict(
                {
                    k: (
                        cls.build(v)
                        if v is not None and type(v).__name__ not in _PRIMITIVE_TYPE_NAMES and not isinstance(v, Enum)
                        else v
                    )
                    for k, v in obj.items()
                }
            )
        elif obj is not None and type(obj).__name__ not in _PRIMITIVE_TYPE_NAMES and not isinstance(obj, Enum):
            cls._unsupported_object_error(obj)

    @classmethod
    def validate(cls, obj) -> None:
        """Validate against schema (invoked by init_all after all init methods are called)."""
        # TODO: Support other dataclass-like frameworks
        class_name = TypeUtil.name(obj)
        if is_dataclass(obj):
            for field in fields(obj):
                field_value = getattr(obj, field.name)
                if field_value is not None:
                    # Check that for the fields that have values, the values are of the right type
                    if not cls._is_instance(field_value, field.type):
                        field_type_name = cls._get_field_type_name(field.type)
                        value_type_name = TypeUtil.name(field_value)
                        if "member_descriptor" not in value_type_name:  # TODO(Roman): Remove when fixed
                            raise RuntimeError(
                                f"""Type mismatch for field '{field.name}' of class {class_name}.
Type in dataclass declaration: {field_type_name}
Type of the value: {TypeUtil.name(field_value)}
Note: In case of containers, type mismatch may be in one of the items.
"""
                            )
                else:
                    default_is_none = field.default is None
                    default_factory_is_missing = field.default_factory is MISSING
                    default_value_not_set = default_is_none and default_factory_is_missing
                    if default_value_not_set and not cls._is_optional(field.type):
                        # Error if a field is None but declared as required
                        raise UserError(f"Field '{field.name}' in class '{class_name}' is required but not set.")

    @classmethod
    def _is_instance(cls, field_value, field_type) -> bool:

        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin is None:
            # If field_type is Any no need to check value
            if field_type is Any:
                return True

            # Not a generic type, consider the possible use of annotation
            if isinstance(field_type, type):
                return isinstance(field_value, field_type)
            elif isinstance(field_type, str):
                field_value_type_name = TypeUtil.name(field_value)
                return field_value_type_name == field_type
            else:
                raise RuntimeError(f"Field type {field_type} is neither a type nor a string.")
        elif origin in [UnionType, Union]:
            if field_value is None:
                return NoneType in args
            else:
                return any(cls._is_instance(field_value, arg) for arg in args)
        elif cls._is_instance(field_value, origin):
            # If the generic has type parameters, check them
            if args:
                if (isinstance(field_value, list) and origin is list) or (
                    isinstance(field_value, tuple) and origin is tuple
                ):
                    return all(cls._is_instance(item, args[0]) for item in field_value)
                elif isinstance(field_value, dict) and origin is dict:
                    return all(
                        isinstance(key, args[0]) and cls._is_instance(value, args[1])
                        for key, value in field_value.items()
                    )
        else:
            # Not an instance of the specified origin
            return False

    @classmethod
    def _is_optional(cls, field_type) -> bool:
        """Return true if None is an valid value for field_type."""
        # Check if the type is a union
        if get_origin(field_type) in [UnionType, Union]:
            # Check if NoneType is one of the arguments in the union
            return NoneType in get_args(field_type)
        else:
            # Type hint is not a union, the value cannot be None
            return False

    @classmethod
    def _get_field_type_name(cls, field_type):
        """Get the name of a type, including handling for Union types."""
        if get_origin(field_type) in [UnionType, Union]:
            return " | ".join(t.__name__ for t in get_args(field_type))
        else:
            return field_type.__name__

    @classmethod
    def _unsupported_object_error(cls, obj: Any) -> None:
        obj_type_name = TypeUtil.name(obj)
        raise RuntimeError(
            f"Class {obj_type_name} cannot be a record or its field. Supported types include:\n"
            f"  1. Slotted classes where all public fields are supported types;\n"
            f"  2. Tuples where all values are supported types;\n"
            f"  3. Dictionaries with string keys where all values are supported types; and\n"
            f"  4. Primitive types from the following list: {', '.join(_PRIMITIVE_TYPE_NAMES)}"
        )
