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
from typing import Any
from typing import Type
from typing import cast
from cl.runtime.records.protocols import TDataDict
from cl.runtime.records.protocols import is_key
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.dict_serializer import handle_optional_annot
from cl.runtime.serialization.string_serializer import StringSerializer
from cl.runtime.serialization.string_serializer import primitive_type_names as str_primitive_type_names

key_serializer = StringSerializer()
"""Serializer for key to string conversion."""


class FlatDictSerializer(DictSerializer):
    """
    Serialization for slot-based classes to flat dict (without nested fields).
    Complex types serialize as a json string.
    """

    primitive_type_names = ["NoneType", "float", "int"]
    """Override primitive_type_names to enable formating for more types."""

    @classmethod
    def _is_json_str(cls, value: str) -> bool:
        """A quick check that a string is most likely JSON."""
        return value.startswith("{") and value.endswith("}")

    def serialize_data(self, data, *, is_root: bool = False):

        if data.__class__.__name__ in self.primitive_type_names:
            return data
        elif data.__class__.__name__ in str_primitive_type_names:
            return StringSerializer.serialize_primitive(data)
        elif is_key(data):
            # Serialize key as string
            key_str = key_serializer.serialize_key(data)
            if self._is_json_str(key_str):
                raise RuntimeError(f"Key str must not match json condition, key_str value: {key_str}.")

            return key_str
        else:
            # All other types try to serialize as JSON string
            json_data = super().serialize_data(data)

            if not isinstance(json_data, (dict, list)):
                raise RuntimeError(
                    f"Received value is not serializable to json. Value: {json_data}, input value: {data}."
                )

            # If it is root, don't serialize to json string
            if is_root:
                return json_data
            else:
                return json.dumps(json_data)

    def deserialize_data(self, data: TDataDict, type_: Type | None = None):

        # Extract inner type if type_ is Optional[...]
        type_ = handle_optional_annot(type_)

        if data.__class__.__name__ == "str":
            data = cast(str, data)

            # TODO (Roman): Remove check for Any when it is no longer supported.
            if type_ is Any:
                return data
            elif type_.__name__ in str_primitive_type_names:
                return StringSerializer.deserialize_primitive(data, type_)
            elif is_key(type_) and not self._is_json_str(data):
                # Deserialize key as string if it is declared as key and is not a JSON string
                return key_serializer.deserialize_key(data, type_)
            else:
                # All other types try to deserialize from JSON string
                json_data = json.loads(data)
                return super().deserialize_data(json_data, type_)
        elif data.__class__.__name__ in super().primitive_type_names:
            # Return primitive types unchanged
            return data
        else:
            # Call deserialize_data from base class
            return super().deserialize_data(data, type_)
