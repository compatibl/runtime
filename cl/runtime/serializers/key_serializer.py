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

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Deque
from typing import Tuple
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import DataProtocol
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.key_format import KeyFormat
from cl.runtime.serializers.serializer import Serializer


@dataclass(slots=True, kw_only=True)
class KeySerializer(Serializer):
    """Roundtrip serialization of object to a flattened sequence, object cannot have sequence fields."""

    key_format: KeyFormat = required()
    """Format of the serialized key."""

    primitive_serializer: Serializer = required()
    """Use to serialize primitive types."""

    enum_serializer: Serializer = required()
    """Use to serialize enum types."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize key into a delimited string or a flattened sequence of primitive types."""

        # Get the class of data, which may be NoneType
        data_class_name = TypeUtil.name(data)

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else None
        is_optional = type_hint.optional if type_hint is not None else None
        remaining_chain = type_hint.remaining if type_hint is not None else None

        # Ensure data type is the same as schema type if type chain is specified
        if schema_type_name is not None and data_class_name != "tuple" and data_class_name != schema_type_name:
            raise RuntimeError(
                f"Key is an instance of type {data_class_name} while schema type is {schema_type_name}.\n"
                f"Substituting records for keys is allowed, but deriving one key type from another is not."
            )
        if remaining_chain:
            key_type_name = "key in tuple format" if data_class_name == "tuple" else f"key class {data_class_name}"
            raise RuntimeError(
                f"Data is an instance of a {key_type_name} that is incompatible with\n"
                f"a composite type hint: {type_hint.to_str()}."
            )

        if data is None:
            if is_optional:
                return None
            else:
                raise RuntimeError(f"Key is None while its type hint {type_hint.to_str()} is not optional.")
        elif is_key(data):
            # Perform checks and flatten into a linear sequence
            sequence = self._to_tuple(data)
        else:
            raise RuntimeError(
                f"{TypeUtil.name(self)} cannot serialize {type(data)}.\n"
                f"The input must be a key object, key tuple or None."
            )

        # Check that all tokens are primitive types
        invalid_tokens = [x for x in sequence if not is_primitive(x) and not is_enum(x)]
        if len(invalid_tokens) > 0:
            invalid_tokens_str = "\n".join(str(x) for x in invalid_tokens)
            raise RuntimeError(
                f"Tuple argument of {TypeUtil.name(self)}.serialize includes non-primitive/non-enum tokens:\n"
                f"{invalid_tokens_str}"
            )

        # Convert the flattened sequence according to the specified KeyFormat
        if (key_format := self.key_format) == KeyFormat.DELIMITED:
            # Convert sequence to a semicolon-delimited string
            return ";".join(sequence)
        if key_format == KeyFormat.TUPLE:
            # Sequence format
            return sequence
        else:
            raise ErrorUtil.enum_value_error(key_format, KeyFormat)

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize key from a delimited string or a flattened sequence of primitive types."""

        # Get schema class from the type hint
        schema_class = type_hint._schema_class

        # Convert to key if a record
        if is_record(schema_class):
            key_type = schema_class.get_key_type()
        elif is_key(schema_class):
            key_type = schema_class
        else:
            raise RuntimeError(
                f"Type {TypeUtil.name(schema_class)} passed to {TypeUtil.name(self)}\n"
                f"is not a key or record type, cannot serialize."
            )

        # Convert argument to a sequence based on the key_format field
        if (key_format := self.key_format) == KeyFormat.DELIMITED:
            # Check the argument is a string
            if not isinstance(data, str):
                raise RuntimeError(
                    f"Key format is DELIMITED but data passed to\n"
                    f"KeySerializer.deserialize method has type {TypeUtil.name(data)}"
                )
            sequence = data.split(";")
        elif key_format == KeyFormat.TUPLE:
            # Check the argument is a sequence
            if not is_sequence(data):
                raise RuntimeError(
                    f"Key format is SEQUENCE but data passed to\n"
                    f"KeySerializer.deserialize method has type {TypeUtil.name(data)}"
                )
            # Check each token and create a deque so popleft is available
            sequence = [self._checked_value(x) for x in data]
        else:
            raise ErrorUtil.enum_value_error(key_format, KeyFormat)

        # Check each token and convert to a deque so popleft is available
        tokens = deque(self._checked_value(x) for x in sequence)

        # Perform deserialization
        key_type_hint = (TypeUtil.name(key_type),)
        result = self._from_sequence(tokens, key_type, key_type_hint, key_type)

        # Check if any tokens are remaining
        if (remaining_length := len(tokens)) > 0:
            raise RuntimeError(
                f"Serialized sequence size for key {key_type.__name__} is long by {remaining_length} tokens."
            )
        return result

    def _to_tuple(self, data: DataProtocol | KeyProtocol | Tuple) -> Tuple[TPrimitive, ...]:
        """Serialize key into a flattened sequence of primitive types."""

        # Check that the argument is a key
        if data is None:
            raise RuntimeError("An inner key field inside a composite key cannot be None.")
        elif is_key(data):
            # Check that the argument is frozen
            data.check_frozen()
            # Get type spec
            type_spec = TypeSchema.for_class(type(data))
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(
                    f"Key serializer cannot serialize '{TypeUtil.name(data)}'\nbecause it is not a slotted class."
                )
            field_dict = type_spec.get_field_dict()
            # Serialize slot values in the order of declaration packing primitive types into size-one lists
            packed_result = tuple(
                (
                    [
                        # Use primitive serializer, specify type name, e.g. long (not class name, e.g. int)
                        self.primitive_serializer.serialize(self._checked_value(v), field_spec.type_hint)
                    ]
                    if (v := getattr(data, k)).__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (
                        [
                            # Use enum serializer, specify enum class
                            self.enum_serializer.serialize(self._checked_value(v), field_spec.type_hint)
                        ]
                        if isinstance(v, Enum)
                        else self._to_tuple(v)
                    )
                )
                for k, field_spec in field_dict.items()
            )
        elif isinstance(data, tuple):
            # Check that the first element is a type or type name string
            if not data:
                raise RuntimeError(
                    "An inner key field inside a composite key cannot be empty.\n"
                    "Its first item must be a key type or type name string."
                )

            # Parse the tuple and get type_spec
            key_type, *primitive_keys = data
            if isinstance(key_type, type):
                type_spec = TypeSchema.for_class(key_type)
            elif isinstance(key_type, str):
                type_spec = TypeSchema.for_type_name(key_type)
            else:
                raise RuntimeError(
                    "If an inner key field inside a composite key is a tuple.\n"
                    "Its first item must be a key type or type name string."
                )
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(
                    f"Key serializer cannot serialize '{TypeUtil.name(data)}'\nbecause it is not a slotted class."
                )
            # Get fields in the order of declaration
            field_dict = type_spec.get_field_dict()
            field_specs = field_dict.values()
            if (primitive_keys_count := len(primitive_keys)) != (field_count := len(field_specs)):
                key_type_name = TypeUtil.name(key_type) if isinstance(key_type, type) else key_type
                raise RuntimeError(
                    f"The number of primitive keys {primitive_keys_count} does not match the number of\n"
                    f"key fields {field_count} for key type {key_type_name}."
                )

            # Serialize slot values in the order of declaration packing primitive types into size-one lists
            packed_result = tuple(
                (
                    [
                        # Use primitive serializer, specify type name, e.g. long (not class name, e.g. int)
                        self.primitive_serializer.serialize(self._checked_value(v), field_spec.type_hint)
                    ]
                    if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                    else (
                        [
                            # Use enum serializer, specify enum class
                            self.enum_serializer.serialize(self._checked_value(v), field_spec.type_hint)
                        ]
                        if isinstance(v, Enum)
                        else self._to_tuple(v)
                    )
                )
                for v, field_spec in zip(primitive_keys, field_specs)
            )
        else:
            raise RuntimeError(
                f"An inner key field {TypeUtil.name(data)} is not a primitive type, enum, tuple or key object."
            )

        # Flatten by unpacking the inner tuples
        result = tuple(token for item in packed_result for token in item)
        return result

    @classmethod
    def _checked_value(cls, value: TObj) -> TObj:
        """Return checked primitive value or enum."""
        if value is None:
            raise RuntimeError("A primitive field or enum inside a key cannot be None.")
        if (class_name := value.__class__.__name__) not in PRIMITIVE_CLASS_NAMES and not isinstance(value, Enum):
            raise RuntimeError(f"Type {class_name} inside key is not a primitive type, enum, or another key.")
        return value

    def _from_sequence(
        self,
        tokens: Deque[TPrimitive],
        field_class: type,
        field_type_hint: TypeHint,
        root_class: type,
    ) -> Any:
        """Deserialize key from a flattened sequence of primitive types."""
        if len(tokens) == 0:
            raise RuntimeError(f"Insufficient serialized sequence size for key {root_class.__name__}.")
        elif is_primitive(field_class):
            # Primitive type, extract one token
            token = tokens.popleft()
            return self.primitive_serializer.deserialize(token, field_type_hint)
        elif is_enum(field_class):
            # Enum type, extract one token
            token = tokens.popleft()
            return self.enum_serializer.deserialize(token, field_type_hint)
        elif is_key(field_class):
            # Key type, extract as many tokens as slots
            type_spec = TypeSchema.for_class(field_class)
            field_dict = type_spec.get_field_dict()
            key_tokens = tuple(
                self._from_sequence(tokens, field_spec.get_class(), field_spec.type_hint, root_class)
                for field_spec in field_dict.values()
            )
            result_type = type_spec.get_class()
            result = result_type(*key_tokens)
            return result.build()
        else:
            raise RuntimeError(
                f"Field type {field_class.__name__} inside key type {root_class.__name__} \n"
                f"is not a primitive type, enum, or another key."
            )
