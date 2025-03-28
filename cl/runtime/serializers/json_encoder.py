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
from typing import Any, Tuple
import orjson
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.serializers.json_output_format_enum import JsonOutputFormatEnum

def orjson_default(obj):
    """Handler for unsupported types in orjson."""
    if isinstance(obj, bytes):
        return obj.hex()  # Convert bytes to string using hex encoding
    raise RuntimeError(f"Object of type {obj.__class__.__name__} is not JSON serializable.")


@dataclass(slots=True, kw_only=True)
class JsonEncoder(Data):
    """Encoding of dictionary to and from JSON."""

    json_output_format: JsonOutputFormatEnum = JsonOutputFormatEnum.PRETTY_PRINT
    """JSON output format (pretty print, compact, etc)."""

    def encode(self, data: Any) -> str:
        """Encode to a JSON string."""

        # Use orjson to serialize the dictionary to JSON string in pretty-print format
        if self.json_output_format == JsonOutputFormatEnum.PRETTY_PRINT:
            option = orjson.OPT_INDENT_2
        elif self.json_output_format == JsonOutputFormatEnum.COMPACT:
            option = None
        else:
            raise ErrorUtil.enum_value_error(self.json_output_format, JsonOutputFormatEnum)

        result = orjson.dumps(data, option=option).decode("utf-8")
        return result

    def decode(self, json_str: str) -> Any:  # noqa
        """Decode from a JSON string."""

        # Use orjson to parse the JSON string into a dictionary
        result = orjson.loads(json_str.encode("utf-8"))
        return result
