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

from cl.runtime.primitive.bool_util import BoolUtil
from cl.runtime.primitive.date_util import DateUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.time_util import TimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.type_util import TypeUtil


class PrimitiveSerializer:
    """Helper class for formatting and concatenating supported types into a string."""

    @classmethod
    def format(cls, value: TPrimitive) -> str:
        """Convert value of a primitive type to string (error message if argument is None)."""
        if value is not None and value != "":
            return cls.format_or_none(value)
        else:
            raise RuntimeError("Argument to PrimitiveSerializer.format method is None or an empty string.")

    @classmethod
    def format_or_none(cls, value: TPrimitive | None) -> str | None:
        """Convert value of a primitive type to string (return None if argument is None)."""
        # Use name because different import libraries are possible for some of the primitive types such as UUID
        match type(value).__name__:
            case "NoneType":
                return None
            case "str":
                # Return None for an empty string
                return value if value else None
            case "float":
                return FloatUtil.format(value)
            case "bool":
                return BoolUtil.format(value)
            case "int":
                return str(value)  # TODO: Use IntUtil
            case "date":
                return DateUtil.to_str(value)
            case "time":
                return TimeUtil.to_str(value)
            case "datetime":
                return DatetimeUtil.to_str(value)
            case "UUID":
                if Timestamp.is_uuid7(value):
                    # Use a format with readable timestamp for UUIDv7 based Timestamp
                    return Timestamp.from_uuid7(value)
                else:
                    # Use conventional serialization for other UUID versions
                    return str(value)
            case "bytes":
                # Base64 encoding for bytes with MIME line wrap convention at 76 characters, remove trailing EOL
                return base64.encodebytes(value).decode('utf-8').rstrip("\n")
            case _:
                raise RuntimeError(
                    f"Type {TypeUtil.name(value)} cannot be converted to string " f"using PrimitiveSerializer.format method."
                )
