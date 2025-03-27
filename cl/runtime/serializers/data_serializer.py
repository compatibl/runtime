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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_CLASS_NAMES
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import SEQUENCE_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.key_serializer import KeySerializer
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.serializers.slots_util import SlotsUtil
from cl.runtime.serializers.type_format_enum import TypeFormatEnum
from cl.runtime.serializers.type_inclusion_enum import TypeInclusionEnum
from cl.runtime.serializers.type_placement_enum import TypePlacementEnum


@dataclass(slots=True, kw_only=True)
class DataSerializer(Data):
    """Roundtrip serialization of object to dictionary with optional type information."""

    primitive_serializer: PrimitiveSerializer = required()
    """Use to serialize primitive types."""

    enum_serializer: EnumSerializer = required()
    """Use to serialize enum types."""

    inner_serializer: KeySerializer | None = None  # TODO: Introduce Serializer base
    """Use to serialize data fields below root level to JSON if specified."""

    key_serializer: KeySerializer | None = None
    """Use to serialize keys to string if specified, otherwise serialize the same way as data fields."""

    type_inclusion: TypeInclusionEnum = TypeInclusionEnum.AS_NEEDED
    """Where to include type information in serialized data."""

    type_format: TypeFormatEnum = TypeFormatEnum.NAME_ONLY
    """Format of the type information in serialized data (optional, do not provide if type_inclusion=OMIT)."""

    type_placement: TypePlacementEnum = TypePlacementEnum.FIRST
    """Placement of type information in the output dictionary (optional, do not provide if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    def serialize(self, data: Any) -> Any:
        """Serialize data to a dictionary."""

        if self.type_inclusion in [TypeInclusionEnum.AS_NEEDED, TypeInclusionEnum.ALWAYS]:
            # Use typed serialization if bidirectional flag is on
            return self._typed_serialize(data, is_root=True)
        elif self.type_inclusion == TypeInclusionEnum.OMIT:
            # Use untyped serialization
            return self._untyped_serialize(data)
        else:
            raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusionEnum)

    def deserialize(self, data: Any) -> Any:
        """Deserialize a dictionary into object using type information extracted from the _type field."""

        if self.type_inclusion in [TypeInclusionEnum.AS_NEEDED, TypeInclusionEnum.ALWAYS]:
            if data is None:
                # Pass through None
                return None
            elif data.__class__.__name__ in MAPPING_TYPE_NAMES:
                # Get type name from the input dict
                if (type_name := data.get(self.type_field, None)) is None:
                    raise RuntimeError(f"Key '_type' is missing in the serialized data, cannot deserialize.")
                # Create type chain of length one from the type
                type_chain = [type_name]
                # Use typed deserialization
                return self._typed_deserialize(data, type_chain)
            elif data is not None and data.__class__.__name__ in SEQUENCE_TYPE_NAMES:
                # Invoke on each item in the sequence
                return list(self.deserialize(v) for v in data)
            else:
                raise RuntimeError(
                    f"Data is not a list or mapping, cannot deserialize without type_chain argument:\n"
                    f"{ErrorUtil.wrap(data)}."
                )
        elif self.type_inclusion == TypeInclusionEnum.OMIT:
            raise RuntimeError("Deserialization is not supported when type_inclusion=NEVER.")
        else:
            raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusionEnum)

    def _typed_serialize(
            self,
            data: Any, type_chain: Tuple[str, ...] | None = None,
            *,
            is_root: bool | None = None,
    ) -> Any:
        """Serialize the argument to a dictionary type_chain and schema."""

        # Get type and class of data and parse type chain
        data_class_name = data.__class__.__name__ if data is not None else None
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
                    f"a typed serializer without specifying a type chain."
                    f"For a primitive value, the type chain is required and must have\n"
                    f"the size of one with primitive type at position 0."
                )

            if schema_type_name in PRIMITIVE_TYPE_NAMES:
                # Deserialize using primitive serializer if specified
                return self.primitive_serializer.serialize(data, [schema_type_name])
            else:
                # Parse as enum
                type_spec = TypeSchema.for_type_name(schema_type_name)
                if not isinstance(type_spec, EnumSpec):
                    raise RuntimeError(
                        f"Schema type '{schema_type_name}' is not a primitive type or enum while"
                        f"the data is an instance of primitive class {data_class_name}:\n"
                        f"{ErrorUtil.wrap(data)}."
                    )
                # Serialize
                enum_class = type_spec.get_class()
                result = self.enum_serializer.serialize(data, enum_class)
                return result
        elif data_class_name in SEQUENCE_TYPE_NAMES:
            # Serialize sequence into list, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the sequence, and will cause an error for a primitive item
            return list(self._typed_serialize(v, remaining_chain) for v in data)  # TODO: Replace by tuple
        elif data_class_name in MAPPING_TYPE_NAMES:
            # Deserialize mapping into dict, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the mapping, and will cause an error for a primitive item
            return dict(
                (k, self._typed_serialize(v, remaining_chain)) for k, v in data.items()
            )  # TODO: Replace by frozendict
        elif is_data(data):

            # Do not apply custom key and inner serializers at root level
            if not is_root:
                if self.key_serializer is not None and is_key(data):
                    # Use key serializer for key types if specified
                    return self.key_serializer.serialize(data)
                elif self.inner_serializer is not None:
                    # Use inner serializer for data below root level if specified
                    return self.inner_serializer.serialize(data)

            # Type spec for the data
            data_type_spec = TypeSchema.for_class(data.__class__)
            data_type_name = data_type_spec.type_name
            if not isinstance(data_type_spec, DataSpec):
                raise RuntimeError(f"Type '{schema_type_name}' is not a slotted class.")

            # Perform check against the schema if provided irrespective of the type inclusion setting
            if schema_type_name is not None and schema_type_name != data_type_name:
                # If schema type is specified, ensure that data is an instance of the specified type
                schema_type_spec = TypeSchema.for_type_name(schema_type_name)
                schema_type_name = schema_type_spec.type_name
                if not isinstance(schema_type_spec, DataSpec):
                    raise RuntimeError(f"Type '{schema_type_name}' is not a slotted class.")
                if not isinstance(data, schema_type_spec.get_class()):
                    raise RuntimeError(
                        f"Type {data_type_name} is not the same or a subclass of "
                        f"the type {schema_type_name} specified in schema."
                    )

            # Include type in output according to the type_inclusion setting
            if self.type_inclusion == TypeInclusionEnum.ALWAYS:
                include_type = True
            elif self.type_inclusion == TypeInclusionEnum.AS_NEEDED:
                # Include if schema type is not provided or not the same as data type
                include_type = schema_type_name is None or schema_type_name != data_type_name
            elif self.type_inclusion == TypeInclusionEnum.OMIT:
                include_type = False
            else:
                raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusionEnum)

            # Parse type_format field
            if self.type_inclusion != TypeInclusionEnum.OMIT:
                if self.type_format == TypeFormatEnum.NAME_ONLY:
                    type_field = data_type_name
                elif self.type_format == TypeFormatEnum.FULL_PATH:
                    raise RuntimeError("TypeFormatEnum.FULL_PATH is not supported.")
                else:
                    raise ErrorUtil.enum_value_error(self.type_format, TypeFormatEnum)
            else:
                type_field = None

            # Parse type_placement field
            if self.type_inclusion != TypeInclusionEnum.OMIT:
                if self.type_placement == TypePlacementEnum.FIRST:
                    include_type_first = include_type
                    include_type_last = False
                elif self.type_placement == TypePlacementEnum.LAST:
                    include_type_first = False
                    include_type_last = include_type
                else:
                    raise ErrorUtil.enum_value_error(self.type_placement, TypePlacementEnum)
            else:
                include_type_first = False
                include_type_last = False

            # # Include type information first based on include_type_first flag
            result = {self.type_field: type_field} if include_type_first else {}

            # Get class and field dictionary for schema_type_name
            data_field_dict = data_type_spec.get_field_dict()

            # Serialize slot values in the order of declaration except those that are None
            result.update(
                {
                    k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k): (
                        self.primitive_serializer.serialize(v, field_spec.type_chain)
                        if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (
                            self.enum_serializer.serialize(v, field_spec.get_class())
                            if isinstance(v, Enum)
                            else self._typed_serialize(v, field_spec.type_chain)
                        )
                    )
                    for k, field_spec in data_field_dict.items()
                    if (v := getattr(data, k)) is not None
                }
            )

            if include_type_last:
                # Include type information last based on include_type_last flag
                result[self.type_field] = type_field
            return result
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def _typed_deserialize(self, data: Any, type_chain: Tuple[str, ...]) -> Any:
        """Deserialize data using type_chain and schema."""

        # Parse type chain
        type_name, is_optional, remaining_chain = TypeUtil.unpack_type_chain(type_chain)

        if data is None:
            # Return None if is_optional flag is set, otherwise raise an error
            if is_optional:
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_chain[0]} indicates it is required.")
        elif type_name in PRIMITIVE_TYPE_NAMES:
            # Check that no type chain is remaining
            if remaining_chain:
                raise RuntimeError(f"Primitive type {type_name} has type chain {', '.join(remaining_chain)} remaining.")
            # Deserialize primitive type using primitive serializer if specified, otherwise return raw data
            return self.primitive_serializer.deserialize(data, [type_name])
        elif type_name in SEQUENCE_TYPE_NAMES:
            if not remaining_chain:
                raise RuntimeError(
                    f"Inner type not specified for the sequence type {type_name}.\n"
                    f"Use type_name[Any] to specify a sequence with any item type."
                )
            # Deserialize sequence into tuple
            return list(self._typed_deserialize(v, remaining_chain) for v in data)
        elif type_name in MAPPING_TYPE_NAMES:
            if not remaining_chain:
                raise RuntimeError(
                    f"Inner type not specified for the mapping type {type_name}.\n"
                    f"Use type_name[str, Any] to specify a mapping with any value type."
                )
            # Deserialize mapping into frozendict
            # TODO: Replace by frozendict
            return {
                k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k): self._typed_deserialize(
                    v, remaining_chain
                )
                for k, v in data.items()
            }
        elif isinstance(data, str) or isinstance(data, Enum):
            # Process as enum if data is a string or enum, after checking that schema type is not primitive
            type_spec = TypeSchema.for_type_name(type_name)
            type_class = type_spec.get_class()
            if is_key(type_class) and self.key_serializer is not None:
                # Use key serializer to deserialize
                return self.key_serializer.deserialize(data, type_class)
            elif is_data(type_class) and self.inner_serializer is not None:
                # Use inner serializer to deserialize
                return self.inner_serializer.deserialize(data, type_class)
            elif isinstance(type_spec, EnumSpec):
                # Check that no type chain is remaining
                if remaining_chain:
                    raise RuntimeError(f"Enum type {type_name} has type chain {', '.join(remaining_chain)} remaining.")
                # Deserialize
                result = self.enum_serializer.deserialize(data, type_class)
                return result
            else:
                raise RuntimeError(
                    f"Type '{type_name}' cannot be deserialized\n"
                    f"from the following string or enum:\n{ErrorUtil.wrap(data)}."
                )
        elif data.__class__.__name__ in MAPPING_TYPE_NAMES:
            # Process as slotted class if data is a mapping but schema type is not
            # Get _type if provided, otherwise use type_name
            data_type_name = data.get(self.type_field, None)
            if data_type_name is not None and data_type_name != type_name:
                type_name = data_type_name

            # Deserialize slotted type if data is a mapping
            type_spec = TypeSchema.for_type_name(type_name)
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(f"Type '{type_name}' cannot be deserialized from a dictionary.")

            # Check that no type chain is remaining
            if len(type_chain) > 1:
                raise RuntimeError(f"Slotted type {type_name} has type chain {', '.join(remaining_chain)} remaining.")

            # Get class and field dictionary for type_name
            type_class = type_spec.get_class()
            field_dict = type_spec.get_field_dict()

            # Deserialize into a dict
            result_dict = {
                (
                    snake_case_k := k if not self.pascalize_keys else CaseUtil.pascal_to_snake_case(k)
                ): self._typed_deserialize(v, field_dict[snake_case_k].type_chain)
                for k, v in data.items()
                if not k.startswith("_") and v is not None
            }

            # Construct an instance of the target type
            result = type_class(**result_dict)

            # Invoke build and return
            return result.build()
        else:
            raise RuntimeError(
                f"Cannot deserialize the following data into type '{type_name}':\n" f"{ErrorUtil.wrap(data)}"
            )

    def _untyped_serialize(self, data: Any) -> Any:
        """
        Serialize slotted classes, primitive types, and supported dict- and list-like containers
        without using the schema or including _type in output.
        """

        if data is None:
            # Pass through None
            return None
        elif (data_class_name := data.__class__.__name__) in PRIMITIVE_CLASS_NAMES:
            # Primitive type, serialize using primitive serializer if specified, otherwise return raw data
            return self.primitive_serializer.serialize(data)
        elif data_class_name in SEQUENCE_CLASS_NAMES:
            # Sequence container, including items that are None in output to preserve item positions
            result = [
                (
                    None
                    if v is None
                    else (
                        self.primitive_serializer.serialize(v)
                        if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._untyped_serialize(v))
                    )
                )
                for v in data
            ]
            return result
        elif data_class_name in MAPPING_CLASS_NAMES:
            # Mapping container, do not include values that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    self.primitive_serializer.serialize(v)
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._untyped_serialize(v))
                )
                for k, v in data.items()
                if v is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        elif isinstance(data, Enum):
            # Enum type, serialize using enum serializer if specified, otherwise return raw data
            return self.enum_serializer.serialize(data)
        elif is_data(data):
            # Slotted class, get slots from this class and its bases in the order of declaration from base to derived
            slots = SlotsUtil.get_slots(type(data))
            # Serialize slot values in the order of declaration except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    self.primitive_serializer.serialize(v)
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._untyped_serialize(v))
                )
                for k in slots
                if (v := getattr(data, k)) is not None and not k.startswith("_")
            }
            return result
        else:
            # Did not match a supported data type
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")
