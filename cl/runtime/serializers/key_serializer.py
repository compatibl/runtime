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

from cl.runtime.records.build_util import BuildUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES, TObj, is_record, is_key_or_record, KeyProtocol, \
    TPrimitive, is_key
from cl.runtime.records.protocols import is_data
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.type_schema import TypeSchema
from cl.runtime.serializers.enum_serializer import EnumSerializer
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer


@dataclass(slots=True, kw_only=True)
class KeySerializer(Data):
    """Roundtrip serialization of object to a flattened sequence, object cannot have sequence fields."""

    delimited: bool = required()
    """Return a delimited string instead of a tuple if set (optional, defaults to True)."""

    primitive_serializer: PrimitiveSerializer = required()
    """Use to serialize primitive types."""

    enum_serializer: EnumSerializer = required()
    """Use to serialize enum types."""

    def serialize(self, data: KeyProtocol) -> Any:
        """
        Serialize data into a delimited string or flattened sequence based on delimited flag,
        validating against type_chain if provided.
        """

        # Convert to key if record
        if is_record(data):
            data = data.get_key()

        # Check and invoke the helper method
        sequence = self._to_sequence(self._checked_key(data))

        # Return a delimited string or sequence depending on settings
        if self.delimited:
            return ";".join(sequence)
        else:
            return sequence

    def _to_sequence(self, data: Any) -> Tuple[Any, ...]:
        """Serialize data into a flattened sequence."""

        # Get type spec
        type_spec = TypeSchema.for_class(type(data))
        if not isinstance(type_spec, DataSpec):
            raise RuntimeError(f"Key serializer cannot serialize '{TypeUtil.name(data)}'\n"
                               f"because it is not a slotted class.")
        field_dict = type_spec.get_field_dict()

        # Serialize slot values in the order of declaration packing primitive types into size-one lists
        packed_result = tuple(
            (
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
                else self._to_sequence(self._checked_key(v))
            )
            for k, field_spec in field_dict.items()
            if not k.startswith("_")
        )
        # Flatten by unpacking the inner tuples
        result = tuple(token for item in packed_result for token in item)
        return result

    @classmethod
    def _checked_value(cls, value: TObj) -> TObj:
        if value is None:
            raise RuntimeError("A primitive field or enum inside a key cannot be None.")
        if (class_name := value.__class__.__name__) not in PRIMITIVE_CLASS_NAMES and not isinstance(value, Enum):
            raise RuntimeError(f"Type {class_name} inside key is not a primitive type, enum, or another key.")
        return value

    @classmethod
    def _checked_key(cls, key: TObj) -> TObj:
        if key is None:
            raise RuntimeError("A field inside a key cannot be None.")
        if not is_key(key):
            raise RuntimeError(f"Type {TypeUtil.name(key)} inside key is not a primitive type, enum, or another key.")
        BuildUtil.check_frozen(key)
        return key
