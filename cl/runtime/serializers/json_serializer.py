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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.json_format import JsonFormat
from cl.runtime.serializers.serializer import Serializer


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True, frozen=True)
class JsonSerializer(Serializer):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    data_serializer: Serializer | None = None
    """Serializes data into dictionary from which it is serialized into JSON."""

    json_output_format: JsonFormat = JsonFormat.PRETTY_PRINT
    """JSON output format (pretty print, compact, etc)."""

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize to a JSON string."""

        # Use self.dict_serializer to serialize the data to a dictionary
        data_dict = self.data_serializer.serialize(data, type_hint)

        # Use orjson to serialize the dictionary to JSON string in pretty-print format
        if self.json_output_format == JsonFormat.PRETTY_PRINT:
            option = orjson.OPT_INDENT_2
        elif self.json_output_format == JsonFormat.COMPACT:
            option = None
        else:
            raise ErrorUtil.enum_value_error(self.json_output_format, JsonFormat)

        result = orjson.dumps(data_dict, option=option).decode("utf-8")
        return result

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a JSON string into an object if bidirectional flag is set, and to a dictionary if not."""

        # TODO: Validate type_hint

        # Use orjson to parse the JSON string into a dictionary
        json_dict = orjson.loads(data.encode("utf-8"))

        # Use self.dict_serializer to deserialize from the dictionary
        result = self.data_serializer.deserialize(json_dict, type_hint)
        return result
