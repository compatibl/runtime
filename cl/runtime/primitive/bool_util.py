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

from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil


class BoolUtil:
    """Helper methods for working with booleans."""

    @classmethod
    def parse_required_bool(
        cls, field_value: str | None, *, field_name: str | None = None
    ) -> bool:  # TODO: Move to Util class
        """Parse an optional boolean value."""
        match field_value:
            case None | "":
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f"for field {field_name}" if field_name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} is empty. Valid values are Y or N.")
            case "Y":
                return True
            case "N":
                return False
            case _:
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f" for field {field_name}" if field_name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} must be Y, N or an empty string.\nField value: {field_value}")

    @classmethod
    def parse_optional_bool(
        cls, field_value: str | None, *, field_name: str | None = None
    ) -> bool | None:  # TODO: Move to Util class
        """Parse an optional boolean value."""
        match field_value:
            case None | "":
                return None
            case "Y":
                return True
            case "N":
                return False
            case _:
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f" for field {field_name}" if field_name is not None else ""
                raise UserError(f"The value{for_field} must be Y, N or an empty string.\nField value: {field_value}")
