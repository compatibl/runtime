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
from typing import Any
import orjson
from cl.runtime.primitive.primitive_serializers import PrimitiveSerializers
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True)
class JsonSerializer(Data):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    bidirectional: bool | None = None
    """Use schema to validate and include _type in output to support both serialization and deserialization."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _dict_serializer: DictSerializer2 | None = None
    """Serializes data into dictionary from which it is serialized into JSON."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self._dict_serializer is None:
            self._dict_serializer = DictSerializer2(
                bidirectional=self.bidirectional,
                pascalize_keys=self.pascalize_keys,
                primitive_serializer=PrimitiveSerializers.DEFAULT,
            ).build()

    def serialize(self, data: Any) -> str:
        """Serialize to a JSON string."""

        # Use self.dict_serializer to serialize the data to a dictionary
        data_dict = self._dict_serializer.serialize(data)

        # Use orjson to serialize the dictionary to JSON string in pretty-print format
        result = orjson.dumps(data_dict, option=orjson.OPT_INDENT_2).decode()
        return result

    def deserialize(self, json_str: str) -> Any:
        """Deserialize a JSON string into an object if bidirectional flag is set, and to a dictionary if not."""

        # Use orjson to parse the JSON string into a dictionary
        json_dict = orjson.loads(json_str.encode("utf-8"))

        # Use self.dict_serializer to deserialize from the dictionary
        result = self._dict_serializer.deserialize(json_dict)
        return result
