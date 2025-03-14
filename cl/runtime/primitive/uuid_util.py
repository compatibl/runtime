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

from uuid import UUID


class UuidUtil:
    """Helper methods for any UUID versions. Use TimestampUtil for methods specific to UUID version 7."""

    @classmethod
    def to_str(cls, value: UUID) -> str:
        """Serialize any UUID version to string with standard 8-4-4-4-12 formatting after checking its type."""
        if type(value).__name__ == "UUID":
            return str(value)
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to UuidUtil.to_str method which expects UUID.")

    @classmethod
    def from_str(cls, value: str) -> UUID:
        """Deserialize any UUID version from string."""
        if isinstance(value, str):
            try:
                # Try to parse as UUID
                result = UUID(value)
            except ValueError:
                raise RuntimeError(f"Cannot parse string '{value}' as UUID.")
        else:
            raise RuntimeError(f"Class {type(value).__name__} is passed to UuidUtil.from_str method which expects str.")
        return result
