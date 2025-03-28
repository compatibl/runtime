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

INT32_MIN: Final[int] = -(2 ** 31)
"""Minimum value of 32-bit signed integer."""

INT32_MAX: Final[int] = 2 ** 31 - 1
"""Maximum value of 32-bit signed integer."""

LONG_64_MIN: Final[int] = -(2 ** 63)
"""Minimum value of 64-bit signed integer."""

LONG_64_MAX: Final[int] = 2 ** 63 - 1
"""Maximum value of 64-bit signed integer."""

LONG_54_MIN: Final[int] = -(2 ** 53)
"""Minimum value of 54-bit signed integer, numbers in this range can be represented as a float exactly."""

LONG_54_MAX: Final[int] = 2 ** 53 - 1
"""Maximum value of 54-bit signed integer, numbers in this range can be represented as a float exactly."""

def check_int_32(value: int | float | None) -> None:
    """Error message if the value does not fit in 32-bit signed integer range, pass through None."""
    if value is not None and (value < INT32_MIN or value > INT32_MAX):
        raise RuntimeError(
            f"Integer {value} value does not fit in 32-bit signed integer range, "
            f"use long (64-bit signed integer) type instead."
        )

def check_int_64(value: int | float | None) -> None:
    """Error message if the value does not fit in 32-bit signed integer range, pass through None."""
    if value is not None and (value < LONG_64_MIN or value > LONG_64_MAX):
        raise RuntimeError(f"The value {value} does not fit in 64-bit signed integer (signed long) range\n"
                           f"from {LONG_64_MIN} to {LONG_64_MAX}.")

def check_int_54(value: int | float | None) -> None:
    """Error message if the value does not fit in 54-bit signed integer range, pass through None."""
    if value is not None and (value < LONG_54_MIN or value > LONG_54_MAX):
        raise RuntimeError(f"The value {value} cannot be represented as a float exactly because it does not fit\n"
                           f"in 54-bit signed integer range from {LONG_54_MIN} to {LONG_54_MAX}.")
