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

from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.limits import check_int_32


class IntUtil:
    """Helper methods for int class."""

    @classmethod
    def to_str(cls, value: int) -> str:
        """Serialize int to string after checking it is an int that fits in 32-bit signed integer range."""
        if isinstance(value, int):
            check_int_32(value)
            return str(value)
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to IntUtil.to_str method which expects int.\n"
                               f"None is not a valid value.")

    @classmethod
    def from_str(cls, value: str) -> int:
        """Deserialize int from string and check it fits in 32-bit signed integer range."""
        if isinstance(value, str):
            try:
                # Try to parse as int
                result = int(value)
                check_int_32(result)
                return result
            except ValueError:
                raise RuntimeError(f"Cannot parse string '{value}' as int.")
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to IntUtil.from_str method which expects str.\n"
                               f"None is not a valid value.")

    @classmethod
    def from_float(cls, value: float) -> int:
        """
        Check that float value is within roundoff tolerance from an int and return the int, error otherwise.
        Verifies that the value fits in 32-bit signed integer range.
        """
        result = FloatUtil.to_int(value)
        return result

