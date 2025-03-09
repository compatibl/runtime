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

import orjson
from dataclasses import dataclass
from typing import Any
from cl.runtime.serialization.dict_serializer_2 import DictSerializer2


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True, frozen=True)
class JsonSerializer:
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _dict_serializer: DictSerializer2 = None
    """Serializes data into dictionary from which it is serialized into JSON."""

    def __post_init__(self):
        """Perform setup."""
        _dict_serializer = DictSerializer2(pascalize_keys=self.pascalize_keys)

    def to_json(self, data: Any) -> str:
        """
        Serialize a slots-based object to a JSON string without using the schema or retaining type information,
        not suitable for deserialization.
        """
        # Convert to dict with serialize_primitive flag set
        data_dict = self._dict_serializer.to_dict(data, serialize_primitive=True)

        # Use orjson to serialize the dictionary to JSON in pretty-print format
        result = orjson.dumps(data_dict, option=orjson.OPT_INDENT_2).decode()
        return result
