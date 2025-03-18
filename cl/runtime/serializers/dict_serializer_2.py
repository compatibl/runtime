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
from typing import Any, Sequence
from typing import Type
from frozendict import frozendict

from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES, MAPPING_TYPE_NAMES, \
    PRIMITIVE_TYPE_NAMES, PRIMITIVE_CLASS_NAMES
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.serializers.slots_util import SlotsUtil


@dataclass(slots=True, kw_only=True)
class DictSerializer2(Freezable):
    """Roundtrip serialization of object to dictionary with optional type information."""

    primitive_serializer: PrimitiveSerializer | None = None
    """Use to serialize primitive types if set, otherwise leave primitive types unchanged."""

    enum_serializer: EnumSerializer | None = None
    """Use to serialize enum types if set, otherwise leave enum types unchanged."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    bidirectional: bool | None = None
    """Use schema to validate and include _type in output to support both serialization and deserialization."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.enum_serializer is None:
            # Create an EnumSerializer with default settings if not specified
            self.enum_serializer = EnumSerializer().build()

    def serialize(self, data: Any) -> Any:
        """Serialize data to a dictionary."""

        if self.bidirectional:
            # Use typed serialization if bidirectional flag is on
            return self._typed_serialize(data)
        else:
            # Otherwise use untyped serialization
            return self._untyped_serialize(data)

    def deserialize(self, data) -> Any:
        """Deserialize a dictionary into object using _type key and schema."""
        if self.bidirectional:
            # Get type name from the input dict
            if (type_name := data.get("_type", None)) is None:
                raise RuntimeError(f"Key '_type' is missing in the serialized data, cannot deserialize.")
            # Create type chain of length one from the type
            type_chain = [type_name]
            # Use typed deserialization
            return self._typed_deserialize(data, type_chain)
        else:
            raise RuntimeError(f"Deserialization is not supported when {self.__class__.__name__}.bidirectional\n"
                               f"flag is not set.")

    def _typed_serialize(self, data: Any, schema_type: Type | None = None) -> Any:
        """
        Serialize a slots-based object to a dictionary.

        Args:
            data: Data to serialize which may be a slotted class, sequence, or mapping where
                  leaf nodes are primitive types from the supported list or enums
            schema_type: Type specified in the schema in 'type_name' or 'type_name | None' string format (optional)
        """

        if getattr(data, "__slots__", None) is not None:

            # If type is specified, ensure that data is an instance of the specified type
            if schema_type and not isinstance(data, schema_type):
                obj_type_name = TypeUtil.name(data.__class__)
                schema_type_name = TypeUtil.name(schema_type)
                raise RuntimeError(
                    f"Type {obj_type_name} is not the same or a subclass of "
                    f"the type {schema_type_name} specified in schema."
                )

            # Write type information if type_ is not specified or not the same as type of data
            if schema_type is None or schema_type is not data.__class__:
                type_name = TypeUtil.name(data.__class__)
                result = {"_type": type_name}
            else:
                result = {}

            # Get slots from this class and its bases in the order of declaration from base to derived
            slots = SlotsUtil.get_slots(data.__class__)

            # Serialize slot values in the order of declaration except those that are None
            result.update(
                {
                    (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                        (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                        if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (
                            (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                            if isinstance(v, Enum)
                            else self.serialize(v)
                        )
                    )
                    for k in slots
                    if (v := getattr(data, k)) is not None and (not hasattr(v, "__len__") or len(v) > 0)
                }
            )
            return result
        elif isinstance(data, list) or isinstance(data, tuple):
            # Assume that type of the first item is the same as for the rest of the collection
            is_primitive_collection = len(data) > 0 and data[0].__class__.__name__ in PRIMITIVE_CLASS_NAMES
            if is_primitive_collection:
                # More efficient implementation for a primitive collection
                if self.primitive_serializer is not None:
                    return [self.primitive_serializer.serialize(v) for v in data]
                else:
                    return data
            else:
                # Not a primitive collection, serialize elements one by one
                result = [
                    (
                        None
                        if v is None  # TODO: Single level if/else in the following lines
                        else (
                            (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                            if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                            else (
                                (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                                if isinstance(v, Enum)
                                else self.serialize(v)
                            )
                        )
                    )
                    for v in data
                ]
            return result
        elif isinstance(data, dict) or isinstance(data, frozendict):
            # Dictionary, return with serialized values except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    None
                    if v is None else
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES else
                    (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                    if isinstance(v, Enum) else
                    self.serialize(v)
                )
                for k, v in data.items()
                if not hasattr(v, "__len__") or len(v) > 0
            }
            return result
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def _typed_deserialize(self, data: Any, type_chain: Sequence[str]) -> Any:
        """Deserialize data using type_chain and schema."""

        # At least one item in type chain is required
        type_hint = type_chain[0]

        # Parse type hint to get type name and optional flag
        type_tokens = type_chain[0].split("|")
        if len(type_tokens) == 2 and type_tokens[1].strip() == "None":
            type_name = type_tokens[0].strip()
            is_optional = True
        elif len(type_tokens) == 1:
            type_name = type_tokens[0].strip()
            is_optional = False
        else:
            raise RuntimeError(f"Type hint {type_hint} does not follow the format 'type_name' or 'type_name | None'.")

        if data is None:
            # Return None if is_optional flag is set, otherwise raise an error
            if is_optional:
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_hint} is not optional.")
        elif type_name in PRIMITIVE_TYPE_NAMES:
            # Check that no type chain is remaining
            if len(type_chain) > 1:
                remaining_chain_str = ", ".join(type_chain[1:])
                raise RuntimeError(f"Primitive type {type_name} has type chain {remaining_chain_str} remaining.")
            # Deserialize primitive type using primitive serializer if specified, otherwise return raw data
            if self.primitive_serializer:
                return self.primitive_serializer.deserialize(data, type_name)
            else:
                return data
        elif type_name in SEQUENCE_TYPE_NAMES:
            if len(type_chain) == 1:
                raise RuntimeError(f"Inner type not specified for the sequence type {type_name}.\n"
                                   f"Use type_name[Any] to specify a sequence with any item type.")
            # Deserialize sequence into tuple
            remaining_chain = type_chain[1:]
            return list(self._typed_deserialize(v, remaining_chain) for v in data)  # TODO: Replace by tuple
        elif type_name in MAPPING_TYPE_NAMES:
            if len(type_chain) == 1:
                raise RuntimeError(f"Inner type not specified for the mapping type {type_name}.\n"
                                   f"Use type_name[str, Any] to specify a mapping with any value type.")
            # Deserialize mapping into frozendict
            remaining_chain = type_chain[1:]
            return dict((k, self._typed_deserialize(v, remaining_chain)) for k, v in data.items())  # TODO: Replace by frozendict
        elif isinstance(data, str):
            # Parse as enum if data is a string
            type_spec = TypeSchema.for_type_name(type_name)
            if isinstance(type_spec, EnumSpec):
                # Check that no type chain is remaining
                if len(type_chain) > 1:
                    remaining_chain_str = ", ".join(type_chain[1:])
                    raise RuntimeError(f"Enum type {type_name} has type chain {remaining_chain_str} remaining.")
                # Deserialize
                enum_class = type_spec.get_class()
                result = self.enum_serializer.deserialize(data, enum_class)
                return result
            else:
                raise RuntimeError(f"Type '{type_name}' cannot be deserialized from the following string:\n"
                                   f"{ErrorUtil.wrap(data)}.")
        elif data.__class__.__name__ in MAPPING_TYPE_NAMES:

            # Get _type if provided, otherwise use type_name
            data_type_name = data.pop("_type", None)
            if data_type_name is not None and data_type_name != type_name:
                type_name = data_type_name
    
            # Deserialize slotted type if data is a mapping
            type_spec = TypeSchema.for_type_name(type_name)
            if isinstance(type_spec, DataSpec):
                # Check that no type chain is remaining
                if len(type_chain) > 1:
                    remaining_chain_str = ", ".join(type_chain[1:])
                    raise RuntimeError(f"Slotted type {type_name} has type chain {remaining_chain_str} remaining.")

                # Get class and field dictionary for type_name
                type_class = type_spec.get_class()
                field_dict = type_spec.get_field_dict()
    
                # Deserialize into a dict
                result_dict = {
                    k: self._typed_deserialize(v, field_dict[k].type_chain)
                    for k, v in data.items()
                    if not k.startswith("_") and v is not None and (not hasattr(v, "__len__") or len(v) > 0)
                }
                # Construct an instance of the target type
                result = type_class(**result_dict)
                return result
            else:
                raise RuntimeError(f"Type '{type_name}' cannot be serialized from a dictionary.")
        else:
            raise RuntimeError(f"Cannot deserialize the following data into type '{type_name}':\n"
                               f"{ErrorUtil.wrap(data)}")

    def _untyped_serialize(self, data: Any) -> Any:
        """
        Serialize slotted classes, primitive types, and supported dict- and list-like containers
        without using the schema or including _type in output.
        """

        if getattr(data, "__slots__", None) is not None:
            # Slotted class, get slots from this class and its bases in the order of declaration from base to derived
            slots = SlotsUtil.get_slots(data.__class__)
            # Serialize slot values in the order of declaration except those that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (
                        (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                        if isinstance(v, Enum)
                        else self.serialize(v)
                    )
                )
                for k in slots
                if (v := getattr(data, k)) is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        elif isinstance(data, list) or isinstance(data, tuple):
            # Sequence container, including items that are None in output to preserve item positions
            result = [
                (
                    None
                    if v is None
                    else (
                        (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                        if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (
                            (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                            if isinstance(v, Enum)
                            else self.serialize(v)
                        )
                    )
                )
                for v in data
            ]
            return result
        elif isinstance(data, dict) or isinstance(data, frozendict):
            # Mapping container, do not include values that are None
            result = {
                (k if not self.pascalize_keys else CaseUtil.snake_to_pascal_case(k)): (
                    (self.primitive_serializer.serialize(v) if self.primitive_serializer is not None else v)
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (
                        (self.enum_serializer.serialize(v) if self.enum_serializer is not None else v)
                        if isinstance(v, Enum)
                        else self.serialize(v)
                    )
                )
                for k, v in data.items()
                if v is not None and (not hasattr(v, "__len__") or len(v) > 0)
            }
            return result
        else:
            # Did not match a supported data type
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")