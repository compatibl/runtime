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
from typing import Type, Deque
from typing import Tuple
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES, TPrimitive, is_sequence, is_primitive
from cl.runtime.records.protocols import DataProtocol
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.key_format_enum import KeyFormatEnum
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer


@dataclass(slots=True, kw_only=True)
class KeySerializer(Data):
    """Roundtrip serialization of object to a flattened sequence, object cannot have sequence fields."""

    key_format: KeyFormatEnum = required()
    """Format of the serialized key."""

    primitive_serializer: PrimitiveSerializer = required()
    """Use to serialize primitive types."""

    enum_serializer: EnumSerializer = required()
    """Use to serialize enum types."""

    def serialize(self, data: DataProtocol | KeyProtocol) -> str | Tuple[TPrimitive, ...]:
        """Serialize key into a delimited string or a flattened sequence of primitive types."""

        # Convert to key if a record
        if is_record(data):
            # Build the data before getting the key
            data.build()
            # The returned key should be frozen, this will be checked below
            data = data.get_key()
        elif is_key_or_record(data):
            # Build the key (this has no effect if already frozen)
            data.build()
        else:
            raise RuntimeError(
                f"Type {TypeUtil.name(data)} passed to {TypeUtil.name(self)} is not a key or record, cannot serialize."
            )

        # Perform checks and convert to a sequence
        sequence = self._to_sequence(data)

        if (key_format := self.key_format) == KeyFormatEnum.FLATTENED_SEQUENCE:
            return sequence
        elif key_format == KeyFormatEnum.FLATTENED_STRING:
            # Convert sequence to a semicolon-delimited string
            return ";".join(sequence)
        else:
            raise ErrorUtil.enum_value_error(key_format, KeyFormatEnum)

    def deserialize(self, data: str | Tuple[TPrimitive, ...], key_type: Type[KeyProtocol]) -> KeyProtocol:
        """Deserialize key from a delimited string or a flattened sequence of primitive types."""

        # Convert argument to a sequence based on the key_format field
        if (key_format := self.key_format) == KeyFormatEnum.FLATTENED_SEQUENCE:
            # Check the argument is a sequence
            if not is_sequence(data):
                raise RuntimeError(
                    f"Key format is FLATTENED_SEQUENCE but data passed to\n"
                    f"KeySerializer.deserialize method has type {TypeUtil.name(data)}")
            # Check each token and create a deque so popleft is available
            sequence = [self._checked_value(x) for x in data]
        elif key_format == KeyFormatEnum.FLATTENED_STRING:
            # Check the argument is a string
            if not isinstance(data, str):
                raise RuntimeError(
                    f"Key format is FLATTENED_STRING but data passed to\n"
                    f"KeySerializer.deserialize method has type {TypeUtil.name(data)}")
            sequence = data.split(";")
        else:
            raise ErrorUtil.enum_value_error(key_format, KeyFormatEnum)

        # Check each token and convert to a deque so popleft is available
        tokens = deque(self._checked_value(x) for x in sequence)

        # Perform deserialization
        result = self._from_sequence(tokens, key_type, key_type)

        # Check if any tokens are remaining
        if (remaining_length := len(tokens)) > 0:
            raise RuntimeError(
                f"Serialized sequence size for key {key_type.__name__} is long by {remaining_length} tokens.")
        return result

    def _to_sequence(self, data: DataProtocol | KeyProtocol) -> Tuple[TPrimitive, ...]:
        """Serialize key into a flattened sequence of primitive types."""

        # Check that the argument is a key
        if data is None:
            raise RuntimeError("An inner key field inside a composite key cannot be None.")
        elif not is_key(data):
            raise RuntimeError(f"Type {TypeUtil.name(data)} inside key is not a primitive type, enum, or another key.")

        # Check that the argument is frozen
        BuildUtil.check_frozen(data)

        # Get type spec
        type_spec = TypeSchema.for_class(type(data))
        if not isinstance(type_spec, DataSpec):
            raise RuntimeError(
                f"Key serializer cannot serialize '{TypeUtil.name(data)}'\nbecause it is not a slotted class."
            )
        field_dict = type_spec.get_field_dict()

        # Serialize slot values in the order of declaration packing primitive types into size-one lists
        packed_result = tuple(
            [
                # Use primitive serializer, specify type name, e.g. long (not class name, e.g. int)
                self.primitive_serializer.serialize(self._checked_value(v), field_spec.type_chain)
            ]
            if (v := getattr(data, k)).__class__.__name__ in PRIMITIVE_CLASS_NAMES
            else
            [
                # Use enum serializer, specify enum class
                self.enum_serializer.serialize(self._checked_value(v), field_spec.get_class())
            ]
            if isinstance(v, Enum)
            else self._to_sequence(v)
            for k, field_spec in field_dict.items()
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
            field_class: Type[KeyProtocol],
            root_class: Type[KeyProtocol]
    ) -> KeyProtocol:
        """Deserialize key from a flattened sequence of primitive types."""
        if len(tokens) == 0:
            raise RuntimeError(f"Insufficient serialized sequence size for key {root_class.__name__}.")
        elif is_primitive(field_class):
            # Primitive type, extract one token
            token = tokens.popleft()
            return self.primitive_serializer.deserialize(token, [field_class.__name__])
        elif isinstance(field_class, Enum):
            # Enum type, extract one token
            token = tokens.popleft()
            return self.enum_serializer.deserialize(token, field_class)
        elif is_key(field_class):
            # Key type, extract as many tokens as slots
            type_spec = TypeSchema.for_class(field_class)
            field_dict = type_spec.get_field_dict()
            key_tokens = tuple(
                self._from_sequence(tokens, field_spec.get_class(), root_class)
                for field_spec in field_dict.values()
            )
            result_type = type_spec.get_class()
            result = result_type(*key_tokens)
            return result
        else:
            raise RuntimeError(
                f"Field type {field_class.__name__} inside key type {root_class.__name__} \n"
                f"is not a primitive type, enum, or another key.")
