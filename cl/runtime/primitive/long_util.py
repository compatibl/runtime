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

class LongUtil:
    """Helper methods for the long (64-bit signed integer) type stored in int class."""

    @classmethod
    def to_str(cls, value: int) -> str:
        """Serialize long (64-bit signed integer) to string."""
        if isinstance(value, int):
            return str(value)
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to LongUtil.to_str method which expects int.")

    @classmethod
    def from_str(cls, value: str) -> int:
        """Deserialize long (64-bit signed integer) from string."""
        if isinstance(value, str):
            try:
                # Try to parse as int
                result = int(value)
            except ValueError:
                raise RuntimeError(f"Cannot parse string '{value}' as int.")
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to LongUtil.from_str method which expects str.")
        return result
