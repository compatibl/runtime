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
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_format_enum import TypeFormatEnum
from cl.runtime.serializers.type_inclusion_enum import TypeInclusionEnum


def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True)
class JsonSerializer(Data):
    """Serialization without using the schema or retaining type information, not suitable for deserialization."""

    type_inclusion: TypeInclusionEnum = required()
    """Where to include type information in serialized data."""

    type_format: TypeFormatEnum | None = None
    """Format of the type information in serialized data (optional, do not provide if type_inclusion=OMIT)."""

    type_field: str = "_type"
    """Dictionary key under which type information is stored (optional, defaults to '_type')."""

    pascalize_keys: bool | None = None
    """Pascalize keys during serialization if set."""

    _dict_serializer: DataSerializer | None = None
    """Serializes data into dictionary from which it is serialized into JSON."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        self._dict_serializer = DataSerializer(
            type_inclusion=self.type_inclusion,
            type_format=self.type_format,
            type_field=self.type_field,
            pascalize_keys=self.pascalize_keys,
            primitive_serializer=PrimitiveSerializers.DEFAULT,
            enum_serializer=EnumSerializers.DEFAULT,
        ).build()

    def serialize(self, data: Any) -> str:
        """Serialize to a JSON string."""

        # Use self.dict_serializer to serialize the data to a dictionary
        data_dict = self._dict_serializer.serialize(data)

        # Use orjson to serialize the dictionary to JSON string in pretty-print format
        result = orjson.dumps(data_dict, option=orjson.OPT_INDENT_2).decode("utf-8")
        return result

    def deserialize(self, json_str: str) -> Any:
        """Deserialize a JSON string into an object if bidirectional flag is set, and to a dictionary if not."""

        if self.type_inclusion == TypeInclusionEnum.OMIT:
            raise RuntimeError("Deserialization is not supported when type_inclusion=NEVER.")

        # Use orjson to parse the JSON string into a dictionary
        json_dict = orjson.loads(json_str.encode("utf-8"))

        # Use self.dict_serializer to deserialize from the dictionary
        result = self._dict_serializer.deserialize(json_dict)
        return result
