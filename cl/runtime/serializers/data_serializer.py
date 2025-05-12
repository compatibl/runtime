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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.data_util import DataUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_CLASS_NAMES
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import SEQUENCE_AND_MAPPING_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.encoder import Encoder
from cl.runtime.serializers.serializer import Serializer
from cl.runtime.serializers.type_format import TypeFormat
from cl.runtime.serializers.type_inclusion import TypeInclusion
from cl.runtime.serializers.type_placement import TypePlacement


@dataclass(slots=True, kw_only=True)
class DataSerializer(Serializer):
    """Roundtrip serialization of object to dictionary with optional type information."""

    primitive_serializer: Serializer = required()
    """Use to serialize primitive types."""

    enum_serializer: Serializer = required()
    """Use to serialize enum types."""

    key_serializer: Serializer | None = None
    """Use to serialize key fields if specified, otherwise serialize the same way as data fields."""

    inner_serializer: Serializer | None = None
    """Use to serialize data fields, if specified the current serializer will only be used at root level."""

    inner_encoder: Encoder | None = None
    """Encode the output of inner serializer if specified."""

    type_inclusion: TypeInclusion = TypeInclusion.AS_NEEDED
    """Where to include type information in serialized data."""

    type_format: TypeFormat = TypeFormat.NAME_ONLY
    """Format of the type information in serialized data (optional, do not provide if type_inclusion=OMIT)."""

    type_placement: TypePlacement = TypePlacement.FIRST
    """Placement of type information in the output dictionary (optional, do not provide if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    def __validate(self) -> None:
        """Perform checks without changing the data."""
        if (self.inner_serializer is not None) ^ (self.inner_encoder is not None):
            raise ErrorUtil.mutually_required_fields_error(
                ["inner_serializer", "inner_encoder"], class_name=self.__class__.__name__
            )

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize the argument to a dictionary type_hint and schema."""

        if self.type_inclusion not in [TypeInclusion.AS_NEEDED, TypeInclusion.ALWAYS, TypeInclusion.OMIT]:
            raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusion)

        # Get the class of data, which may be NoneType
        data_class_name = TypeUtil.name(data)

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None
        remaining_chain = type_hint.remaining if type_hint is not None else None

        if data_class_name == "NoneType":
            if type_hint is None or is_optional:
                # Return None if type hint is not specified or is_optional flag is set, otherwise raise an error
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_hint.to_str()} indicates it is required.")
        elif data_class_name in PRIMITIVE_CLASS_NAMES:
            if remaining_chain:
                raise RuntimeError(
                    f"Data is an instance of a primitive class {data_class_name} which is incompatible with type hint\n"
                    f"{type_hint.to_str()}."
                )

            if schema_type_name in PRIMITIVE_TYPE_NAMES:
                # Deserialize using primitive serializer if a primitive type
                return self.primitive_serializer.serialize(data, type_hint)
            else:
                # Otherwise assume it is an enum
                # TODO: Check for type_kind in TypeHint instead
                result = self.enum_serializer.serialize(data, type_hint)
                return result
        elif data_class_name in SEQUENCE_TYPE_NAMES:
            # Serialize sequence into list, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the sequence, and will cause an error for a primitive item
            if type_hint is not None:
                type_hint.validate_for_sequence()
            if len(data) == 0:
                # Consider an empty sequence equivalent to None
                return None
            else:
                return list(self.serialize(v, remaining_chain) for v in data)  # TODO: Replace by tuple
        elif data_class_name in MAPPING_TYPE_NAMES:
            # Deserialize mapping into dict, allowing remaining_chain to be None
            # If remaining_chain is None, it will be provided for each slotted data
            # item in the mapping, and will cause an error for a primitive item
            if type_hint is not None:
                type_hint.validate_for_mapping()
            return dict(
                (self._serialize_key(dict_key), self.serialize(dict_value, remaining_chain))
                for dict_key, dict_value in data.items()
                if not DataUtil.is_empty(dict_value)
            )  # TODO: Replace by frozendict
        elif is_data(data):
            # Use key serializer for key types if specified
            if self.key_serializer is not None and is_key(data):
                return self.key_serializer.serialize(data, type_hint)

            # Type spec for the data
            data_type_spec = TypeSchema.for_class(data)
            data_type_name = data_type_spec.type_name

            # Perform check against the schema if provided irrespective of the type inclusion setting
            if schema_type_name is not None and schema_type_name != data_type_name:
                # If schema type is specified, ensure that data is an instance of the specified type
                schema_type_spec = TypeSchema.for_type_name(schema_type_name)
                schema_type_name = schema_type_spec.type_name
                if not is_data(schema_class := schema_type_spec.get_class()):
                    raise RuntimeError(f"Type '{schema_type_name}' is not a slotted class.")
                if not isinstance(data, schema_class):
                    raise RuntimeError(
                        f"Type {data_type_name} is not the same or a subclass of "
                        f"the type {schema_type_name} specified in schema."
                    )

            # Include type in output according to the type_inclusion setting
            if self.type_inclusion == TypeInclusion.ALWAYS:
                include_type = True
            elif self.type_inclusion == TypeInclusion.AS_NEEDED:
                # Include if schema type is not provided or not the same as data type
                include_type = schema_type_name is None or schema_type_name != data_type_name
            elif self.type_inclusion == TypeInclusion.OMIT:
                include_type = False
            else:
                raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusion)

            # Parse type_format field
            if self.type_inclusion != TypeInclusion.OMIT:
                if self.type_format == TypeFormat.NAME_ONLY:
                    type_field = data_type_name
                elif self.type_format == TypeFormat.FULL_PATH:
                    raise RuntimeError("TypeFormat.FULL_PATH is not supported.")
                else:
                    raise ErrorUtil.enum_value_error(self.type_format, TypeFormat)
            else:
                type_field = None

            # Parse type_placement field
            if self.type_inclusion != TypeInclusion.OMIT:
                if self.type_placement == TypePlacement.FIRST:
                    include_type_first = include_type
                    include_type_last = False
                elif self.type_placement == TypePlacement.LAST:
                    include_type_first = False
                    include_type_last = include_type
                else:
                    raise ErrorUtil.enum_value_error(self.type_placement, TypePlacement)
            else:
                include_type_first = False
                include_type_last = False

            # Include type information first based on include_type_first flag
            result = {self.type_field: type_field} if include_type_first else {}

            # Get class and field dictionary for schema_type_name
            data_field_dict = data_type_spec.get_field_dict()

            # Serialize slot values in the order of declaration except those that are None
            key_serializer = self.key_serializer if self.key_serializer is not None else self
            result.update(
                {
                    self._serialize_key(field_key): (
                        self.primitive_serializer.serialize(field_value, field_spec.type_hint)
                        if field_value.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                        else (
                            self.enum_serializer.serialize(field_value, field_spec.type_hint)
                            if is_enum(field_value)
                            else (
                                key_serializer.serialize(field_value, field_spec.type_hint)
                                if is_key(field_value)
                                else self._serialize_inner(field_value, field_spec.type_hint)
                            )
                        )
                    )
                    for field_key, field_spec in data_field_dict.items()
                    if not DataUtil.is_empty(field_value := getattr(data, field_key))
                }
            )

            if include_type_last:
                # Include type information last based on include_type_last flag
                result[self.type_field] = type_field
            return result
        else:
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize data using type_hint and schema."""

        if self.type_inclusion == TypeInclusion.OMIT:
            raise RuntimeError("Deserialization is not supported when type_inclusion=OMIT.")
        elif self.type_inclusion not in [TypeInclusion.AS_NEEDED, TypeInclusion.ALWAYS]:
            raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusion)

        # Get the class of data, which may be NoneType
        data_class_name = TypeUtil.name(data)

        if type_hint is None:
            if data_class_name in MAPPING_CLASS_NAMES:
                # Attempt to extract type information from the mapping data
                if (type_name := data.get(self.type_field, None) if data else None) is not None:
                    # Type name is specified, look up the class
                    type_spec = TypeSchema.for_type_name(type_name)
                    type_hint = TypeHint.for_class(type_spec.get_class())
                    # Recursive call is needed because of nested containers
                    return self.deserialize(data, type_hint)
                else:
                    raise RuntimeError(
                        f"Key '_type' is missing in the serialized data and type hint is not specified, "
                        f"cannot deserialize."
                    )
            elif data_class_name in SEQUENCE_CLASS_NAMES:
                # Recursive call is needed because type information may be contained inside items
                return [self.deserialize(v) for v in data]
            else:
                raise RuntimeError(
                    f"Data is not a list or mapping, cannot deserialize without type_hint argument:\n"
                    f"{ErrorUtil.wrap(data)}."
                )

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None
        remaining_chain = type_hint.remaining if type_hint is not None else None

        if data_class_name == "NoneType":
            if type_hint is None or is_optional:
                # Return None if type hint is not specified or is_optional flag is set, otherwise raise an error
                return None
            else:
                raise RuntimeError(f"Data is None but type hint {type_hint.to_str()} indicates it is required.")
        elif schema_type_name in PRIMITIVE_TYPE_NAMES:
            type_hint.validate_for_primitive()
            return self.primitive_serializer.deserialize(data, type_hint)
        elif schema_type_name in SEQUENCE_TYPE_NAMES:
            type_hint.validate_for_sequence()
            if data_class_name not in SEQUENCE_CLASS_NAMES:
                raise RuntimeError(
                    f"Data type {data_class_name} is a sequence but schema type\n" f"{schema_type_name} is not."
                )
            # Decode if necessary
            # TODO: Eliminate check for the fist character
            if len(data) == 0:
                # Consider an empty sequence equivalent to None
                return None
            elif self.inner_encoder is not None and isinstance(data, str) and data[0] == "[":
                # Decode and deserialize sequence using data_serializer
                data = self.inner_encoder.decode(data)
                return list(self.inner_serializer.deserialize(v, remaining_chain) for v in data)
            else:
                # Deserialize sequence using self
                return list(self.deserialize(v, remaining_chain) for v in data)
        elif schema_type_name in MAPPING_TYPE_NAMES:
            type_hint.validate_for_mapping()
            # Deserialize mapping into frozendict
            # TODO: Replace by frozendict
            return {
                self._deserialize_key(dict_key): self.deserialize(
                    dict_value, remaining_chain
                )  # TODO: Should data_serializer be used here?
                for dict_key, dict_value in data.items()
                if not DataUtil.is_empty(dict_value)
            }
        elif isinstance(data, str):
            # Process as enum if data is a string or enum, after checking that schema type is not primitive
            type_spec = TypeSchema.for_type_name(schema_type_name)
            schema_class = type_spec.get_class()
            if self.key_serializer is not None and is_key(schema_class):
                if (
                    # TODO: Eliminate check for the fist character
                    self.inner_encoder is not None
                    and len(data) > 0
                    and data[0] == "{"
                ):  # TODO: Fix for non-JSON encoding
                    # Decode data field using data_encoder if provided and deserialize using self
                    decoded_data = self.inner_encoder.decode(data)
                    return self.inner_serializer.deserialize(decoded_data, type_hint)
                else:
                    # Otherwise use key serializer to deserialize
                    return self.key_serializer.deserialize(data, type_hint)
            elif self.inner_encoder is not None and is_data(schema_class):
                # Deserialize using inner_serializer and inner_encoder if provided, otherwise use self
                return self._deserialize_inner(data, type_hint)
            elif is_enum(schema_class):
                # Check that no type chain is remaining
                if remaining_chain:
                    raise RuntimeError(
                        f"Type hint {type_hint.to_str()} is not a container but specifies an inner type."
                    )
                # Deserialize
                result = self.enum_serializer.deserialize(data, type_hint)
                return result
            else:
                raise RuntimeError(
                    f"Type hint '{type_hint.to_str()}' cannot be deserialized\n"
                    f"from the following string or enum data:\n{ErrorUtil.wrap(data)}."
                )
        elif isinstance(data, Enum):
            # Process as enum
            return self.enum_serializer.deserialize(data, type_hint)
        elif data_class_name in MAPPING_TYPE_NAMES:
            # Process as slotted class if data is a mapping but schema type is not
            # Get _type if provided, otherwise use schema_type_name
            data_type_name = data.get(self.type_field, None)
            if data_type_name is not None and data_type_name != schema_type_name:
                type_name = data_type_name
            elif schema_type_name is not None:
                type_name = schema_type_name
            else:
                # TODO: Record container type for a mapping, e.g. frozendict
                raise RuntimeError("Neither schema type nor _type field is provided for a mapping.")

            # Deserialize slotted type if data is a mapping
            type_spec = TypeSchema.for_type_name(type_name)
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(f"Type '{type_name}' cannot be deserialized from a dictionary.")

            # Check that no type chain is remaining
            if type_hint is not None and type_hint.remaining is not None:
                raise RuntimeError(
                    f"Data type {type_name} is not a container but type hint specifies an inner type:\n"
                    f"{type_hint.to_str()}."
                )

            # Get class and field dictionary for type_name
            schema_class = type_spec.get_class()
            field_dict = type_spec.get_field_dict()

            # Deserialize into a dict
            result_dict = {
                (snake_case_k := self._deserialize_key(field_key)): (
                    self.inner_serializer.deserialize(self.inner_encoder.decode(field_value), field_hint)
                    if (
                        (field_hint := field_dict[snake_case_k].type_hint).schema_type_name != "str"
                        and self.inner_encoder is not None
                        and isinstance(field_value, str)
                        and len(field_value) > 0
                        and field_value[0] in ["{", "["]
                    )
                    else self.deserialize(field_value, field_hint)
                )
                for field_key, field_value in data.items()
                if not field_key.startswith("_") and not DataUtil.is_empty(field_value)
            }

            # Construct an instance of the target type
            result = schema_class(**result_dict)

            # Invoke build and return
            return result.build()
        else:
            raise RuntimeError(
                f"Cannot deserialize the following data using type hint '{type_hint.to_str()}':\n"
                f"{ErrorUtil.wrap(data)}"
            )

    @classmethod
    def _is_empty(cls, data: Any) -> bool:
        """Check if the data is None, an empty string, or an empty container."""
        return data in (None, "") or (data.__class__.__name__ in SEQUENCE_AND_MAPPING_CLASS_NAMES and len(data) == 0)

    def _serialize_key(self, field_key: str) -> str:
        """Transform the field key for use in serialization"""
        if self.pascalize_keys:
            return CaseUtil.snake_to_pascal_case_keep_trailing_underscore(field_key)
        else:
            return field_key

    def _deserialize_key(self, field_key: str) -> str:
        """Transform the field key for use in deserialization"""
        if self.pascalize_keys:
            return CaseUtil.pascale_to_snake_case_keep_trailing_underscore(field_key)
        else:
            return field_key

    def _serialize_inner(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Use inner_serializer and inner_encoder if specified, otherwise use current serializer and no encoder."""
        if self.inner_serializer is not None:
            return self.inner_encoder.encode(self.inner_serializer.serialize(data, type_hint))
        else:
            # If inner serializer is not specified, use the current serializer
            return self.serialize(data, type_hint)

    def _deserialize_inner(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Use inner_serializer and inner_encoder if specified, otherwise use current serializer and no encoder."""
        if self.inner_serializer is not None:
            return self.inner_serializer.deserialize(self.inner_encoder.decode(data), type_hint)
        else:
            # If inner serializer is not specified, use the current serializer
            return self.deserialize(data, type_hint)
