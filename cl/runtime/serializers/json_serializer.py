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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.json_output_format import JsonOutputFormat
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_format import TypeFormat
from cl.runtime.serializers.type_inclusion import TypeInclusion


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True)
class JsonSerializer(Data):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    json_output_format: JsonOutputFormat = JsonOutputFormat.PRETTY_PRINT
    """JSON output format (pretty print, compact, etc)."""

    type_inclusion: TypeInclusion = TypeInclusion.AS_NEEDED
    """Where to include type information in serialized data."""

    type_format: TypeFormat = TypeFormat.NAME_ONLY
    """Format of the type information in serialized data (optional, do not provide if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _data_serializer: DataSerializer | None = None
    """Serializes data into dictionary from which it is serialized into JSON."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self._data_serializer = DataSerializer(
            type_inclusion=self.type_inclusion,
            type_format=self.type_format,
            type_field=self.type_field,
            pascalize_keys=self.pascalize_keys,
            primitive_serializer=PrimitiveSerializers.DEFAULT,
            enum_serializer=EnumSerializers.DEFAULT,
        ).build()

    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize to a JSON string."""

        # Use self.dict_serializer to serialize the data to a dictionary
        data_dict = self._data_serializer.serialize(data, type_hint)

        # Use orjson to serialize the dictionary to JSON string in pretty-print format
        if self.json_output_format == JsonOutputFormat.PRETTY_PRINT:
            option = orjson.OPT_INDENT_2
        elif self.json_output_format == JsonOutputFormat.COMPACT:
            option = None
        else:
            raise ErrorUtil.enum_value_error(self.json_output_format, JsonOutputFormat)

        result = orjson.dumps(data_dict, option=option).decode("utf-8")
        return result

    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a JSON string into an object if bidirectional flag is set, and to a dictionary if not."""

        # TODO: Validate type_hint

        if self.type_inclusion == TypeInclusion.OMIT:
            raise RuntimeError("Deserialization is not supported when type_inclusion=NEVER.")

        # Use orjson to parse the JSON string into a dictionary
        json_dict = orjson.loads(data.encode("utf-8"))

        # Use self.dict_serializer to deserialize from the dictionary
        result = self._data_serializer.typed_deserialize(json_dict, type_hint)
        return result
