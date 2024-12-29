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
    """Helper methods for working with bool type."""

    @classmethod
    def format(cls, value: bool) -> str:
        """Serialize True as uppercase 'Y' and False as uppercase 'N', error if argument is None."""
        result = cls.format_or_none(value)
        if result is None:
            raise RuntimeError("Argument of BoolUtil.format is None, use format_or_none to accept.")
        return result

    @classmethod
    def format_or_none(cls, value: bool | None) -> str | None:
        """Serialize True as uppercase 'Y' and False as uppercase 'N', return None if argument is None."""
        if value is None:
            return None
        if type(value) is not bool:
            raise RuntimeError(f"Argument of BoolUtil.format_or_none has type {type(value).__name__}, "
                               f"only bool is accepted.")
        return "Y" if value else "N"

    @classmethod
    def parse(cls, value: str | None, *, name: str | None = None) -> bool:
        """Parse an optional boolean value, param 'name' is used for error reporting only."""
        match value:
            case None | "":
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f"for field {name}" if name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} is empty. Valid values are Y or N.")
            case "Y":
                return True
            case "N":
                return False
            case _:
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f" for field {name}" if name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} must be Y, N or an empty string.\nField value: {value}")

    @classmethod
    def parse_or_none(cls, value: str | None, *, name: str | None = None) -> bool | None:
        """Parse an optional boolean value, param 'name' is used for error reporting only."""
        match value:
            case None | "":
                return None
            case "Y":
                return True
            case "N":
                return False
            case _:
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f" for field {name}" if name is not None else ""
                raise UserError(f"The value{for_field} must be Y, N or an empty string.\nField value: {value}")
