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

from abc import ABC
from abc import abstractmethod
from typing import Any
from cl.runtime.schema.type_hint import TypeHint


class BuilderUtil(ABC):
    """Helper methods for implementing the builder pattern."""

    @classmethod
    @abstractmethod
    def build_(  # TODO: Review the need for an abstract class method
        cls,
        data: Any,
        type_hint: TypeHint | None = None,
        *,
        outer_type_name: str | None = None,
        field_name: str | None = None,
    ) -> Any:
        """
        Validate data against the type hint, init or normalize, and return an immutable copy.

        Notes:
            Method name is build_ to prevent helper classes being classified as data.

        Args:
            data: Input value or data, must match the type hint
            type_hint: Type hint the data must match
            outer_type_name: Name of the data type containing the field for error messages only (optional)
            field_name: Name of the field in the outer type for error messages only (optional)
        """

    @classmethod
    def _get_location_str(  # TODO: Move to a specialized helper class
        cls,
        data_type_name: str,
        type_hint: TypeHint | None = None,
        *,
        outer_type_name: str | None = None,
        field_name: str | None = None,
    ) -> str:
        """Describes the location where the error occurred."""
        outer_type_name_str = f"Field located in: {outer_type_name}\n" if outer_type_name else ""
        field_name_str = f"Field name: {field_name}\n" if field_name else ""
        actual_type_str = f"Actual field type: {data_type_name}\n"
        expected_type_str = f"Expected field type: {type_hint}\n"
        location_str = f"{outer_type_name_str}{field_name_str}{actual_type_str}{expected_type_str}"
        if location_str:
            return f"\nError location:\n{location_str}"
        else:
            return ""
