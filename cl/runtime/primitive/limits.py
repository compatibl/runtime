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

_INT_32_MIN: Final[int] = -(2**31)
"""Minimum value of 32-bit signed integer."""

_INT_32_MAX: Final[int] = 2**31 - 1
"""Maximum value of 32-bit signed integer."""

_INT_54_MIN: Final[int] = -(2**53)
"""Minimum value of 54-bit signed integer, numbers in this range can be represented as a float exactly."""

_INT_54_MAX: Final[int] = 2**53 - 1
"""Maximum value of 54-bit signed integer, numbers in this range can be represented as a float exactly."""


def is_int_32(value: int | float | None) -> bool:  # TODO: ! Rename to add suffix range
    """True if the value is None or fits in 32-bit signed integer range."""
    return value is None or _INT_32_MIN <= value <= _INT_32_MAX


def check_int_32(value: int | float | None) -> None:
    """Error message if the value is not None and does not fit in 32-bit signed integer range."""
    if not is_int_32(value):
        raise RuntimeError(
            f"The value {value} does not fit in the 32-bit signed integer range\n"
            f"from {_INT_32_MIN} to {_INT_32_MAX}, use long type instead."
        )


def is_int_54(value: int | float | None) -> bool:
    """True if the value is None or fits in 54-bit signed integer range."""
    return value is None or _INT_54_MIN <= value <= _INT_54_MAX


def check_int_54(value: int | float | None) -> None:
    """Error message if the value is not None and does not fit in 54-bit signed integer range."""
    if not is_int_54(value):
        raise RuntimeError(
            f"The value {value} cannot be assigned type 'long' because it does not fit\n"
            f"in the 54-bit signed integer range from {_INT_54_MIN} to {_INT_54_MAX}\n"
            f"that can be represented as a float exactly."
        )
