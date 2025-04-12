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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.data_util import DataUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import SEQUENCE_CLASS_NAMES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.encoder import Encoder
from cl.runtime.serializers.serializer import Serializer
from cl.runtime.serializers.slots_util import SlotsUtil


@dataclass(slots=True, kw_only=True)
class ReportingSerializer(Serializer):
    """Unidirectional serialization of object to a dictionary without type information."""

    primitive_serializer: Serializer = required()
    """Use to serialize primitive types."""

    enum_serializer: Serializer = required()
    """Use to serialize enum types."""

    encoder: Encoder | None = None
    """Use to encode the output of serialize method if specified."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary."""

        # Serialize data to a dictionary without encoding
        serialized = self._serialize(data, type_hint)

        # Encode the result if an encoder is provided
        if self.encoder:
            return self.encoder.encode(serialized)
        else:
            return serialized

    def _serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary without encoding."""

        # TODO: Support type hint for validation only

        if data is None:
            # Pass through None for untyped serialization
            return None
        elif (data_class_name := TypeUtil.name(data)) in PRIMITIVE_CLASS_NAMES:
            # Primitive type, serialize using primitive serializer if specified, otherwise return raw data
            return self.primitive_serializer.serialize(data)
        elif data_class_name in SEQUENCE_CLASS_NAMES:
            if len(data) == 0:
                # Consider an empty sequence equivalent to None
                return None
            else:
                # Include items that are None in output to preserve item positions
                result = [
                    (
                        None
                        if v is None
                        else (
                            self.primitive_serializer.serialize(v)
                            if v.__class__.__name__ in PRIMITIVE_CLASS_NAMES
                            else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._serialize(v))
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
                    else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._serialize(v))
                )
                for k, v in data.items()
                if not DataUtil.is_empty(v)
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
                    else (self.enum_serializer.serialize(v) if isinstance(v, Enum) else self._serialize(v))
                )
                for k in slots
                if not DataUtil.is_empty(v := getattr(data, k)) and not k.startswith("_")
            }
            return result
        else:
            # Did not match a supported data type
            raise RuntimeError(f"Cannot serialize data of type '{type(data)}'.")

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a dictionary into object using type information extracted from the _type field."""
        raise RuntimeError(f"{TypeUtil.name(self)} does not support deserialization.")
