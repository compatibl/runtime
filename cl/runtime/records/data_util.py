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

from types import NoneType
from typing import Any
from frozendict import frozendict
from more_itertools import consume
from cl.runtime.primitive.enum_util import EnumUtil
from cl.runtime.primitive.primitive_util import PrimitiveUtil
from cl.runtime.records.builder_util import BuilderUtil
from cl.runtime.records.condition_util import ConditionUtil
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import is_condition
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.protocols import is_empty
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_mapping
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_schema import TypeSchema


class DataUtil(BuilderUtil):
    """Helper methods for build functionality in DataMixin."""

    @classmethod
    def build_(
        cls,
        data: Any,
        type_hint: TypeHint | None = None,
        *,
        outer_type_name: str | None = None,
        field_name: str | None = None,
    ) -> Any:
        # Get parameters from type_hint if specified, otherwise set to None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None
        remaining_chain = type_hint.remaining if type_hint is not None else None

        if is_empty(data):
            if type_hint is None or is_optional:
                # Return None if type hint is not specified or is_optional flag is set, otherwise raise an error
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_hint.to_str()} indicates it is required.")
        elif is_primitive(type(data)):
            if remaining_chain:
                raise RuntimeError(
                    f"Data is an instance of a primitive class {type(data).__name__} which is incompatible with type hint\n"
                    f"{type_hint.to_str()}."
                )
            return PrimitiveUtil.build_(data, type_hint)
        elif is_enum(type(data)):
            if remaining_chain:
                raise RuntimeError(
                    f"Data is an instance of a primitive class {type(data).__name__} which is incompatible\n"
                    f"with type hint {type_hint.to_str()}."
                )
            return EnumUtil.build_(data, type_hint)
        elif is_sequence(type(data)):
            # Serialize sequence into list, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the sequence, and will cause an error for a primitive item
            if type_hint is not None:
                type_hint.validate_for_sequence()  # TODO: Rename to avoid validate_for...
            return tuple(cls.build_(v, remaining_chain) if not is_empty(v) else None for v in data)
        elif is_mapping(type(data)):
            # Deserialize mapping into dict, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the mapping, and will cause an error for a primitive item
            if type_hint is not None:
                type_hint.validate_for_mapping()
            return frozendict((k, cls.build_(v, remaining_chain)) for k, v in data.items() if not is_empty(v))
        elif is_data_key_or_record(type(data)):
            if data.is_frozen():
                # Stop further processing and return if the object has already been frozen to
                # prevent repeat initialization of shared instances
                return data

            # Invoke '__init' in the order from base to derived
            # Keep track of which init methods in class hierarchy were already called
            invoked = set()
            # Reverse the MRO to start from base to derived
            for class_ in reversed(type(data).__mro__):
                # Remove leading underscores from the class name when generating mangling for __init
                # to support classes that start from _ to mark them as protected
                class_init = getattr(class_, f"_{class_.__name__.lstrip('_')}__init", None)
                if class_init is not None and (qualname := class_init.__qualname__) not in invoked:
                    # Add qualname to invoked to prevent executing the same method twice
                    invoked.add(qualname)
                    # Invoke '__init' method if it exists, otherwise do nothing
                    class_init(data)

            # Type spec for the data
            data_type_spec = TypeSchema.for_class(type(data))
            data_type_name = data_type_spec.type_name

            # Perform check against the schema if provided irrespective of the type inclusion setting
            if schema_type_name is not None and schema_type_name != data_type_name:
                # If schema type is specified, ensure that data is an instance of the specified type
                schema_type_spec = TypeSchema.for_type_name(schema_type_name)
                schema_type_name = schema_type_spec.type_name
                if not is_data_key_or_record(schema_class := schema_type_spec.type_):
                    raise RuntimeError(f"Type '{schema_type_name}' is not a slotted class.")
                if not isinstance(data, schema_class):
                    raise RuntimeError(
                        f"Type {data_type_name} is not the same or a subclass of "
                        f"the type {schema_type_name} specified in schema."
                    )

            # Freeze or make immutable all public fields, checking against the schema
            consume(
                setattr(
                    data,
                    field_name := field_spec.field_name,
                    (
                        cls._checked_empty(  # Validates vs. the type hint while is_empty does not
                            field_value,
                            field_spec.field_type_hint,
                            outer_type_name=typename(type(data)),
                            field_name=field_name,
                        )
                        if is_empty(field_value := getattr(data, field_name))
                        else (
                            PrimitiveUtil.build_(
                                field_value,
                                field_spec.field_type_hint,
                                outer_type_name=typename(type(data)),
                                field_name=field_name,
                            )
                            if is_primitive(type(field_value))
                            else (
                                EnumUtil.build_(
                                    field_value,
                                    field_spec.field_type_hint,
                                    outer_type_name=typename(type(data)),
                                    field_name=field_name,
                                )
                                if is_enum(type(field_value))
                                else (
                                    ConditionUtil.build_(
                                        field_value,
                                        field_spec.field_type_hint,
                                        outer_type_name=typename(type(data)),
                                        field_name=field_name,
                                    )
                                    if is_condition(type(field_value))
                                    else cls.build_(
                                        field_value,
                                        field_spec.field_type_hint,
                                        outer_type_name=typename(type(data)),
                                        field_name=field_name,
                                    )
                                )
                            )
                        )
                    ),
                )
                for field_spec in data_type_spec.fields
            )

            # Mark as frozen and return
            return data.mark_frozen()
        else:
            raise cls._unsupported_object_error(data)

    @classmethod
    def _checked_empty(  # Move to NoneUtils
        cls,
        data: Any,
        type_hint: TypeHint | None = None,
        *,
        outer_type_name: str | None = None,
        field_name: str | None = None,
    ) -> NoneType:
        """Returns the same result as is_empty but also validates against the type hint."""

        # Handle None or empty
        NoneChecks.guard_not_none(type_hint)
        if type_hint.optional:
            # Optional, perform full type hint validation if not None
            if data is not None:
                # Get the actual type name of data, which may be a type
                data_class_name = typename(type(data))
                # Get the expected type name, which may include subtypes such as long or timestamp
                schema_type_name = type_hint.schema_type_name if type_hint is not None else None
                if data_class_name != schema_type_name:
                    raise RuntimeError(
                        f"An empty instance of primitive type has type {data_class_name}\n"
                        f"while {schema_type_name} was expected."
                    )
            return None
        else:
            # Required and has empty value, raise an error
            location_str = cls._get_location_str(
                typename(type(data)), type_hint, outer_type_name=outer_type_name, field_name=field_name
            )
            raise RuntimeError(f"Required field is None or an empty primitive type.{location_str}")

    @classmethod
    def _unsupported_object_error(cls, obj: Any) -> Exception:
        obj_type_name = typename(type(obj))
        return RuntimeError(
            f"Class {obj_type_name} cannot be a record or its field. Supported types include:\n"
            f"  1. Classes that implement 'build' method;\n"
            f"  2. Sequence types (list, tuple, etc.) where all values are supported types;\n"
            f"  3. Mapping types (dict, frozendict, etc.) with string keys where all values are supported types;\n"
            f"  4. Enums; and\n5. Primitive types from the following list:\n{', '.join(PRIMITIVE_CLASS_NAMES)}"
        )
