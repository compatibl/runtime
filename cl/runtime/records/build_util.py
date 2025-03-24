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

from enum import Enum
from typing import Any
from typing import Sequence
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.primitive_util import PrimitiveUtil
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.data_spec_util import DataSpecUtil
from cl.runtime.schema.enum_spec import EnumSpec


class BuildUtil:
    """Helper methods for build functionality in DataMixin."""

    @classmethod
    def check_frozen(cls, obj: Any) -> None:
        """Error message if the object is not yet frozen."""
        if not obj.is_frozen():
            raise RuntimeError(f"An instance of {TypeUtil.name(obj)} is not yet frozen, call 'build' method first.")

    @classmethod
    def typed_build(
        cls,
        data: Any,
        type_chain: Sequence[str] | None = None,
    ) -> Any:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Validates root level object against the schema and calls its 'mark_frozen' method
        """
        # Get type and class of data and parse type chain
        data_class_name = type(data).__name__ if data is not None else None
        schema_type_name, is_optional, remaining_chain = TypeUtil.unpack_type_chain(type_chain)

        if data is None:
            # Return None if no type information or is_optional flag is set, otherwise raise an error
            if schema_type_name is None or is_optional:
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_chain[0]} indicates it is required.")
        elif data_class_name in PRIMITIVE_CLASS_NAMES:
            if remaining_chain:
                raise RuntimeError(
                    f"Data is an instance of a primitive class {data_class_name} while type chain\n"
                    f"{', '.join(remaining_chain)} is remaining."
                )
            if schema_type_name is None:
                raise RuntimeError(
                    f"An instance of a primitive class {data_class_name} is passed to\n"
                    f"the BuildUtil.typed_build method without specifying the schema type."
                )

            if schema_type_name in PRIMITIVE_TYPE_NAMES:
                # Check that the class matches the type specified in schema
                PrimitiveUtil.check_type(data, schema_type_name)
                return data
            else:
                # Error if not an enum
                if not isinstance(data, EnumSpec):
                    raise RuntimeError(
                        f"Schema type '{schema_type_name}' is not a primitive type or enum while"
                        f"the data is an instance of primitive class {data_class_name}:\n"
                        f"{ErrorUtil.wrap(data)}."
                    )
        elif data_class_name in SEQUENCE_TYPE_NAMES:
            if not remaining_chain:
                raise RuntimeError(
                    f"Inner type is not specified in schema for the sequence type {data_class_name}.\n"
                    f"Use type_name[Any] to specify a sequence with any item type."
                )
            # TODO: Use tuple instead of list
            return list(cls.typed_build(v, remaining_chain) for v in data)
        elif data_class_name in MAPPING_TYPE_NAMES:
            if not remaining_chain:
                raise RuntimeError(
                    f"Inner type not specified for the mapping type {data_class_name}.\n"
                    f"Use type_name[str, Any] to specify a mapping with any value type."
                )
            # TODO: Use frozendict instead of dict
            return dict((k, cls.typed_build(v, remaining_chain)) for k, v in data.items())
        elif is_data(data):

            # Has slots, process as data, key or record
            if data.is_frozen():
                # Stop further processing and return if the object has been frozen to
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
            data_type_spec = DataSpecUtil.from_class(data)
            data_type_name = data_type_spec.type_name

            if not isinstance(data_type_spec, DataSpec):
                raise RuntimeError(f"Type of data '{schema_type_name}' is not a slotted class in the schema.")

            if (
                False and schema_type_name is not None and schema_type_name != data_type_name
            ):  # TODO: Check when possible
                # If schema type is specified, error if the data is not an instance of the specified type
                raise RuntimeError(
                    f"Type {data_type_name} is not the same or a subclass of "
                    f"the type {schema_type_name} specified in the schema."
                )

            # Get class and field dictionary for schema_type_name
            data_field_dict = data_type_spec.get_field_dict()

            # Apply updates to the data object
            tuple(
                setattr(data, k, cls.typed_build(v, field_spec.type_chain))
                for k, field_spec in data_field_dict.items()
                if (
                    (v := getattr(data, k)) is not None
                    and type(v).__name__ not in PRIMITIVE_CLASS_NAMES
                    and not isinstance(v, Enum)
                    and not k.startswith("_")
                )
            )

            # Mark as frozen to prevent further modifications
            data.mark_frozen()
            return data
        else:
            raise cls._unsupported_object_error(data)

    @classmethod
    def _unsupported_object_error(cls, obj: Any) -> Exception:
        obj_type_name = TypeUtil.name(obj)
        return RuntimeError(
            f"Class {obj_type_name} cannot be a record or its field. Supported types include:\n"
            f"  1. Classes that implement DataProtocol;\n"
            f"  2. Tuples where all values are supported types;\n"
            f"  3. Dictionaries with string keys where all values are supported types; and\n"
            f"  4. Primitive types from the following list: {', '.join(PRIMITIVE_CLASS_NAMES)}"
        )
