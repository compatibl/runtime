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

import json
from enum import Enum
from typing import Any
from typing import Dict
from typing import Tuple
from typing import Type
from typing import cast
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import TDataDict
from cl.runtime.records.protocols import TDataField
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.serializers.annotations_util import AnnotationsUtil
from cl.runtime.serializers.dict_serializer import DictSerializer
from cl.runtime.serializers.dict_serializer import get_type_dict
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.string_serializer import StringSerializer
from cl.runtime.serializers.string_serializer import primitive_type_names as str_primitive_type_names

_KEY_SERIALIZER = KeySerializers.DELIMITED


class FlatDictSerializer(DictSerializer):
    """
    Serialization for slots-based classes to flat dict (without nested fields).
    Complex types serialize as a json string.
    """

    primitive_type_names = ["NoneType", "float", "int"]
    """Override primitive_type_names to enable formating for more types."""

    @classmethod
    def _is_json_str(cls, value: str) -> bool:
        """A quick check that a string is most likely JSON."""
        return value.startswith("{") and value.endswith("}")

    @classmethod
    def _assemble_any(cls, data: TDataField) -> Dict[str, TDataField]:
        """
        Create dict representation of value annotated with 'Any' to keep information about the type after serialization.
        """

        if is_key(data) or is_record(data):
            return {"_value": data, "_rec_or_key": data.__class__.__name__}
        elif data.__class__.__name__ in str_primitive_type_names:
            return {"_value": data, "_prim": data.__class__.__name__}
        else:
            return {"_value": data}

    @classmethod
    def _disassemble_any(cls, data: Dict[str, TDataField]) -> Tuple[TDataField, Type | None]:
        """Extract value and type from dict representation of 'Any' value."""

        value = data.get("_value")
        if type_name := data.get("_rec_or_key"):
            type_dict = get_type_dict()
            type_ = type_dict.get(type_name)
            return value, type_
        elif primitive_type := data.get("_prim"):
            return value, eval(primitive_type)
        else:
            return value, None

    def serialize_data(self, data, annot_type: Type | None = None, *, is_root: bool = False):

        annot_type = AnnotationsUtil.handle_optional_annot(annot_type)

        if annot_type is Any:
            # If field is annotated with 'Any' serialize value to special dict format
            return self.serialize_data(self._assemble_any(data), None, is_root=is_root)

        if data.__class__.__name__ in self.primitive_type_names:
            return data
        elif data.__class__.__name__ in str_primitive_type_names:
            return StringSerializer.serialize_primitive(data)
        elif is_key(data):
            # Serialize key as string
            key_str = _KEY_SERIALIZER.serialize(data)
            if self._is_json_str(key_str):
                raise RuntimeError(f"Key str must not match json condition, key_str value: {key_str}.")

            return key_str
        elif isinstance(data, Enum):
            # Serialize enum value as str name
            return CaseUtil.upper_to_pascal_case(data.name)
        else:
            # All other types try to serialize as JSON string

            # Serialize data with super
            json_data = super().serialize_data(data, annot_type)

            # Don't wrap to JSON if it is root or value is None after super serialization
            if is_root or json_data is None:
                return json_data

            # Expect only certain types to be passed
            if not isinstance(json_data, (list, tuple, dict)):
                raise RuntimeError(
                    f"Received value is not serializable to json. Value: {json_data}, input value: {data}."
                )

            return json.dumps(json_data)

    def deserialize_data(self, data: TDataDict, type_: Type | None = None):

        # Extract inner type if type_ is optional
        type_ = AnnotationsUtil.handle_optional_annot(type_)

        if type_ is Any:
            # Expect 'data' is a special dict representation of the 'Any' value
            # Deserialize 'Any' dict
            deserialized_any = self.deserialize_data(data, dict)

            # Extract value and type of serialized 'Any' value
            any_value, any_type = self._disassemble_any(deserialized_any)

            # Deserialize using extracted properties
            return self.deserialize_data(any_value, any_type)

        if data.__class__.__name__ == "str":
            data = cast(str, data)

            if type_ is None:
                # "type_" is optional for serialization, for example, the type annotation "dict" is valid even without
                # type arguments. If the value is a string and "type_" is None, the value is considered a string.
                return data
            elif type_.__name__ in str_primitive_type_names:
                return StringSerializer.deserialize_primitive(data, type_)
            elif is_key(type_) and not self._is_json_str(data):
                # Deserialize key as string if it is declared as key and is not a JSON string
                return _KEY_SERIALIZER.deserialize(data, type_)
            elif (mro := getattr(type_, "__mro__", None)) and Enum in mro:
                # Deserialize enum value using upper case value
                upper_case_value = CaseUtil.pascal_to_upper_case(data)
                return type_[upper_case_value]
            else:
                # All other types try to deserialize from JSON string
                try:
                    json_data = json.loads(data)
                except:
                    raise RuntimeError(f"Failed to deserialize data from JSON string: {data}.")
                return super().deserialize_data(json_data, type_)
        elif data.__class__.__name__ in super().primitive_type_names:
            # Return primitive types unchanged
            return data
        else:
            # Call deserialize_data from base class
            return super().deserialize_data(data, type_)
