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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.primitive_checks import PrimitiveChecks
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PrimitiveTypes
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import is_abstract
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_kind import TypeKind
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

        # Perform checks and flatten serialized embedded keys into a linear sequence
        sequence = self._to_sequence(data, type_hint, is_outer=True)

        # Check that all tokens are primitive types
        invalid_tokens = [x for x in sequence if not is_primitive(x) and not is_enum(x)]
        if len(invalid_tokens) > 0:
            invalid_tokens_str = "\n".join(str(x) for x in invalid_tokens)
            raise RuntimeError(
                f"Tuple argument of {typename(self)}.serialize includes non-primitive/non-enum tokens:\n"
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

        # For keys, type hint is required
        PrimitiveChecks.guard_not_none(type_hint)

        # Get schema class from the type hint
        schema_type = type_hint._schema_class

        # Convert to key if a record
        if is_key(schema_type):
            key_type = schema_type
        else:
            raise RuntimeError(
                f"Type {typename(schema_type)} passed to {typename(self)}\n" f"is not a key type, cannot serialize."
            )

        # Convert argument to a sequence based on the key_format field
        if (key_format := self.key_format) == KeyFormat.DELIMITED:
            # Check the argument is a string
            if not isinstance(data, str):
                raise RuntimeError(
                    f"KeyFormat.DELIMITED is specified but data passed to\n"
                    f"KeySerializer.deserialize method has type {typename(data)}"
                )
            sequence = data.split(";")
        elif key_format == KeyFormat.TUPLE:
            # Check the argument is a sequence
            if not is_sequence(data):
                raise RuntimeError(
                    f"KeyFormat.SEQUENCE is specified but data passed to\n"
                    f"KeySerializer.deserialize method has type {typename(data)}"
                )
            # Check each token and create a deque so popleft is available
            sequence = [self._checked_value(x) for x in data]
        else:
            raise ErrorUtil.enum_value_error(key_format, KeyFormat)

        # Check each token and convert to a deque so popleft is available
        tokens = deque(self._checked_value(x) for x in sequence)

        # Perform deserialization
        key_type_hint = TypeHint.for_class(key_type)
        result = self._from_sequence(tokens, key_type, key_type_hint, key_type)

        # Check if any tokens are remaining
        if (remaining_length := len(tokens)) > 0:
            raise RuntimeError(
                f"Serialized key {data} for key type {typename(key_type)} has two {remaining_length} extra tokens."
            )
        return result

    def _to_sequence(self, data: KeyMixin, type_hint: TypeHint, *, is_outer: bool) -> tuple[PrimitiveTypes, ...] | None:
        """Serialize key into a flattened sequence of primitive types."""

        if not is_outer:
            # For inner key fields which also have key type, type hint is required
            PrimitiveChecks.guard_not_none(type_hint)

        # Get the class of data, which may be NoneType
        data_type_name = typename(data)

        # Get parameters from the type chain, considering the possibility that it may be None
        schema_type_name = type_hint.schema_type_name if type_hint is not None else data_type_name
        is_optional = type_hint.optional if type_hint is not None else None
        remaining_chain = type_hint.remaining if type_hint is not None else None

        # Ensure data type is the same as schema type if type chain is specified
        if schema_type_name is not None and data_type_name != schema_type_name:
            # Confirm that schema type is parent of data type
            parent_type_names = TypeCache.get_parent_type_names(data_type_name, type_kind=TypeKind.KEY)
            if not parent_type_names or schema_type_name not in parent_type_names:
                raise RuntimeError(
                    f"Key type {data_type_name} is not a subclass of the field type {schema_type_name}.\n"
                )
            # Confirm that schema type is abstract
            schema_type = TypeCache.from_type_name(schema_type_name)
            if not is_abstract(schema_type):
                raise RuntimeError(
                    f"Key field is declared as {schema_type_name} which neither a key type nor abstract.\n"
                )
            # Field type is parent of the key type rather than the key type itself, include type prefix in key
            key_type_prefix = data_type_name
        else:
            # Key type and field type are the same, do not include type prefix in key
            key_type_prefix = None

        # Ensure that type hint is not a container
        if remaining_chain:
            raise RuntimeError(
                f"Cannot serialize type {data_type_name} because it is\n"
                f"incompatible with container type hint {type_hint.to_str()}."
            )

        if data is None:
            if is_optional:
                if is_outer:
                    return None
                else:
                    # This message will not be displayed for the entire key if type hint allows optional
                    raise RuntimeError("An inner key field inside a composite key cannot be None.")
            else:
                raise RuntimeError(f"Key is None while its type hint {type_hint.to_str()} is not optional.")
        elif is_key(data):

            # Check that the argument is frozen
            data.check_frozen()

            # Get type spec
            type_spec = TypeSchema.for_class(type(data))
            if not isinstance(type_spec, DataSpec):
                raise RuntimeError(
                    f"Key serializer cannot serialize '{typename(data)}' because it is not a data, key or record class."
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
                        else self._to_sequence(v, field_spec.type_hint, is_outer=False)
                    )
                )
                for k, field_spec in field_dict.items()
            )

            # Flatten by unpacking the inner tuples
            result = tuple(token for item in packed_result for token in item)

            # Add key type prefix if schema type is not the same as data type
            if key_type_prefix:
                result = (key_type_prefix,) + result

            return result
        else:
            if is_outer:
                raise RuntimeError(f"{typename(self)} cannot serialize {type(data)} because it is not a key.")
            else:
                # This message will not be displayed for outer key
                raise RuntimeError(
                    f"A field inside a composite key has type {typename(data)}\n"
                    f"which is not a primitive type, enum, or another key."
                )

    def _from_sequence(
        self,
        tokens: Deque[PrimitiveTypes],
        schema_type: type,
        schema_type_hint: TypeHint,
        root_class: type,
    ) -> Any:
        """Deserialize key from a flattened sequence of primitive types."""
        if len(tokens) == 0:
            raise RuntimeError(f"Insufficient number of key tokens for key {root_class.__name__}.")
        elif is_primitive(schema_type):
            # Primitive type, extract one token
            token = tokens.popleft()
            return self.primitive_serializer.deserialize(token, schema_type_hint)
        elif is_enum(schema_type):
            # Enum type, extract one token
            token = tokens.popleft()
            return self.enum_serializer.deserialize(token, schema_type_hint)
        elif is_key(schema_type):

            # Get data type if key field is abstract
            if is_abstract(schema_type):
                # Abstract key class, the first token is data type
                data_type_name = tokens.popleft()
                data_type = TypeCache.from_type_name(data_type_name)
                if not issubclass(data_type, schema_type):
                    raise RuntimeError(
                        f"Key type {data_type_name} is not a subclass of the field type {typename(schema_type)}.\n"
                    )
                elif not is_key(data_type):
                    raise RuntimeError(f"Key value type {data_type} is not a key type.\n")
            else:
                # Field type and data type are the same, no prefix in key
                data_type = schema_type

            type_spec = TypeSchema.for_class(data_type)
            field_dict = type_spec.get_field_dict()
            key_tokens = tuple(
                self._from_sequence(tokens, field_spec.get_class(), field_spec.type_hint, root_class)
                for field_spec in field_dict.values()
            )
            result = data_type(*key_tokens)
            return result.build()
        else:
            raise RuntimeError(
                f"Field type {typename(schema_type)} inside key type {typename(root_class)} \n"
                f"is not a primitive type, enum, or another key."
            )

    @classmethod
    def _checked_value(cls, value: TObj) -> TObj:
        """Return checked primitive value or enum."""
        if value is None:
            raise RuntimeError("A primitive field or enum inside a key cannot be None.")
        if (class_name := value.__class__.__name__) not in PRIMITIVE_CLASS_NAMES and not isinstance(value, Enum):
            raise RuntimeError(f"Type {class_name} inside key is not a primitive type, enum, or another key.")
        return value
