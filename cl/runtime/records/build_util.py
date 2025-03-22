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
from typing import Any, Sequence
from frozendict import frozendict
from cl.runtime.primitive.primitive_util import PrimitiveUtil
from cl.runtime.records.protocols import TObj, is_data, is_primitive
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2


class BuildUtil:
    """Helper methods for build functionality in DataMixin."""

    @classmethod
    def check_frozen(cls, obj: Any) -> None:
        """Error message if the object is not yet frozen."""
        if not obj.is_frozen():
            raise RuntimeError(f"An instance of {TypeUtil.name(obj)} is not yet frozen, call 'build' method first.")

    @classmethod
    def typed_build(cls, data: Any, type_chain: Sequence[str] | None = None) -> Any:
        """
        This method performs the following steps:
        (1) Invokes 'build' recursively for all non-primitive public fields and container elements
        (2) Invokes '__init' method of this class and its ancestors in the order from base to derived
        (3) Validates root level object against the schema and calls its 'mark_frozen' method
        """
        # Get type and class of data and parse type chain
        data_class_name = data.__class__.__name__ if data is not None else None
        schema_type_name, is_optional, remaining_chain = DictSerializer2.unpack_type_chain(type_chain)

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
                # Parse as enum
                type_spec = TypeSchema.for_type_name(schema_type_name)
                if not isinstance(type_spec, EnumSpec):
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
            # Serialize sequence into list
            return tuple(data.typed_build(v, remaining_chain) for v in data)
        elif data_class_name in MAPPING_TYPE_NAMES:
            if not remaining_chain:
                raise RuntimeError(
                    f"Inner type not specified for the mapping type {data_class_name}.\n"
                    f"Use type_name[str, Any] to specify a mapping with any value type."
                )
            # Deserialize mapping into dict
            return frozendict((k, data.typed_build(v, remaining_chain)) for k, v in data.items())
        elif is_data(data):

            # Type spec for the data
            data_type_spec = TypeSchema.for_class(data.__class__)
            data_type_name = data_type_spec.type_name
            if not isinstance(data_type_spec, DataSpec):
                raise RuntimeError(f"Type of data '{schema_type_name}' is not a slotted class in the schema.")

            if schema_type_name is not None and schema_type_name != data_type_name:
                # If schema type is specified, ensure that data is an instance of the specified type
                schema_type_spec = TypeSchema.for_type_name(schema_type_name)
                schema_type_name = schema_type_spec.type_name
                if not isinstance(schema_type_spec, DataSpec):
                    raise RuntimeError(f"Declared type '{schema_type_name}' is not a slotted class in the schema.")
                if not isinstance(data, schema_type_spec.get_class()):
                    raise RuntimeError(
                        f"Type {data_type_name} is not the same or a subclass of "
                        f"the type {schema_type_name} specified in the schema."
                    )

            # Get class and field dictionary for schema_type_name
            data_field_dict = data_type_spec.get_field_dict()

            # Updates for the data object
            update_items = [
                (k, cls.typed_build(v, field_spec.type_chain))
                for k, field_spec in data_field_dict.items()
                if (v := getattr(data, k)) is not None and not is_primitive(v) and not isinstance(v, Enum) and not k.startswith("_")
            ]
            for k, v in update_items:
                setattr(data, k, v)
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
