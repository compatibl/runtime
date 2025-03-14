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

from typing import Final


class IntUtil:
    """Helper methods for int class."""

    INT32_MIN: Final[int] = -2 ** 31
    """Minimum value of 32-bit signed integer."""

    INT32_MAX: Final[int] = 2 ** 31 - 1
    """Maximum value of 32-bit signed integer."""

    @classmethod
    def to_str(cls, value: int) -> str:
        """Serialize int to string after checking it is an int that fits in 32-bit signed integer range."""
        if isinstance(value, int):
            cls.check_range(value)
            return str(value)
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to IntUtil.to_str method which expects int.")

    @classmethod
    def from_str(cls, value: str) -> int:
        """Deserialize int from string and check it fits in 32-bit signed integer range."""
        if isinstance(value, str):
            try:
                # Try to parse as int
                result = int(value)
            except ValueError:
                raise RuntimeError(f"Cannot parse string '{value}' as int.")
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to IntUtil.from_str method which expects str.")

        # Check that the value fits in 32-bit signed integer range
        cls.check_range(result)
        return result

    @classmethod
    def check_range(cls, value: int) -> None:
        """Error message if the value does not fit in 32-bit signed integer range."""
        if value < cls.INT32_MIN or value > cls.INT32_MAX:
            raise RuntimeError(f"Integer {value} value does not fit in 32-bit signed integer range, "
                               f"use long (64-bit signed integer) type instead.")
