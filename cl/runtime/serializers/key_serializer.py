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

from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Tuple
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer


@dataclass(slots=True, kw_only=True)
class KeySerializer(Data):
    """Roundtrip serialization of object to a flattened sequence, object cannot have sequence fields."""

    primitive_serializer: PrimitiveSerializer | None = None
    """Use to serialize primitive types if set, otherwise leave primitive types unchanged."""

    enum_serializer: EnumSerializer | None = None
    """Use to serialize enum types if set, otherwise leave enum types unchanged."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.enum_serializer is None:
            # Create an EnumSerializer with default settings if not specified
            self.enum_serializer = EnumSerializers.DEFAULT

    def serialize(self, data: Any, type_chain: Tuple[str, ...] | None = None) -> Any:
        """Serialize data into a flattened sequence, validating against type_chain if provided."""

        # Get type and class of data and parse type chain
        schema_type_name, is_optional, remaining_chain = TypeUtil.unpack_type_chain(type_chain)

        if data is None:
            # Return None if no type information or is_optional flag is set, otherwise raise an error
            if schema_type_name is None or is_optional:
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_chain[0]} indicates it is required.")
        elif is_data(data):
            # Check that schema type matches the data type, inheritance is not permitted
            data_type_name = TypeUtil.name(data)
            if schema_type_name is not None and schema_type_name != data_type_name:
                # If schema type is specified, ensure that data is an instance of the specified type
                raise RuntimeError(
                    f"Schema type {schema_type_name} is not the same as data type {data_type_name},\n"
                    f"cannot serialize because substituting a derived type is not permitted for\n"
                    f"serializing into a flattened sequence.\n"
                )

            # Type spec for the data (not the schema, because we already checked the types are the same)
            type_spec = TypeSchema.for_class(type(data))
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(
                    f"Schema type '{schema_type_name}' is not a slotted class while data type {data_type_name} is."
                )
            field_dict = type_spec.get_field_dict()

            # Serialize slot values in the order of declaration packing primitive types into size-one lists
            packed_result = tuple(
                (
                    v
                    if (v := getattr(data, k)) is None
                    else (
                        [
                            # Use primitive serializer, specify type name, e.g. long (not class name, e.g. int)
                            (
                                self.primitive_serializer.serialize(v, field_spec.type_chain)
                                if self.primitive_serializer is not None
                                else v
                            )
                        ]
                        if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (
                            [
                                # Use enum serializer, specify enum class
                                (
                                    self.enum_serializer.serialize(v, field_spec.get_class())
                                    if self.enum_serializer is not None
                                    else v
                                )
                            ]
                            if isinstance(v, Enum)
                            else self.serialize(v, field_spec.type_chain)
                        )
                    )
                )
                for k, field_spec in field_dict.items()
                if not k.startswith("_")
            )
            # Flatten by unpacking the inner tuples
            result = tuple(token for item in packed_result for token in item)
            return result
        else:
            raise RuntimeError(
                f"Cannot serialize data of type '{type(data)}' into a flattened sequence\n"
                f"because it is not a slotted class or None."
            )
