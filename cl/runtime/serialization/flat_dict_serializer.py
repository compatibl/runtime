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

import base64
import datetime as dt
import json
from typing import Type
from typing import cast
from uuid import UUID
from cl.runtime.records.protocols import TDataDict
from cl.runtime.records.protocols import is_key
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.string_serializer import StringSerializer

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

        if data.__class__.__name__ in ("date", "datetime", "time"):
            # Serialize date types to iso string
            return data.isoformat()
        elif data.__class__.__name__ == "UUID":
            # Serialize UUID to string
            return str(data)
        elif data.__class__.__name__ == "bytes":
            # Decode bytes to base64 string
            return base64.b64encode(data).decode()
        elif data.__class__.__name__ == "bool":
            # Serialize bool to Y/N char
            return "Y" if data else "N"
        elif is_key(data):
            # Serialize key as string
            key_str = key_serializer.serialize_key(data)
            if self._is_json_str(key_str):
                raise RuntimeError(f"Key str must not match json condition, key_str value: {key_str}.")

            return key_str
        elif data.__class__.__name__ in super().primitive_type_names:
            # If the data does not match the previous conditions
            # and is a primitive for the base class, return unchanged.
            return data
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
        type_ = self._handle_optional_annot(type_)

        if data.__class__.__name__ == "str":
            data = cast(str, data)
            if type_ is None or type_.__name__ == "str":
                # Return unchanged if declared type is string
                return data
            elif type_.__name__ == "datetime":
                # Deserialize datetime from iso string
                return dt.datetime.fromisoformat(data)
            elif type_.__name__ == "date":
                # Deserialize date from iso string
                return dt.date.fromisoformat(data)
            elif type_.__name__ == "time":
                # Deserialize time from iso string
                return dt.time.fromisoformat(data)
            elif type_.__name__ == "bool":
                # Deserialize bool from string
                if (bool_value := True if data == "Y" else False if data == "N" else None) is not None:
                    return bool_value
                else:
                    raise RuntimeError(f"Serialized boolean field has value {data} but only Y/N and 1/0 are allowed.")
            elif type_.__name__ == "UUID":
                # Create UUID from string
                return UUID(data)
            elif type_.__name__ == "bytes":
                # Encode base64 string to bytes
                return base64.b64decode(data.encode())
            elif type_.__name__ == "int":
                # Support string value for declared as int
                return int(data)
            elif type_.__name__ == "float":
                # Support string value for declared as float
                return float(data)
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
