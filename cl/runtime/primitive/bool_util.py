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
from cl.runtime.records.type_util import TypeUtil


class BoolUtil:
    """Helper methods for working with bool type."""

    @classmethod
    def format(cls, value: bool) -> str:
        """Serialize True as lowercase 'true' and False as lowercase 'false', error if argument is None."""
        result = cls.serialize(value)
        if result is None:
            raise RuntimeError("Argument of BoolUtil.format is None, use serialize to accept.")
        return result

    @classmethod
    def serialize(cls, value: bool | None) -> str | None:
        """Serialize True as lowercase 'true' and False as lowercase 'false', return None if argument is None."""
        if value is None:
            return None  # TODO: Review if it should be "null"
        if type(value) is not bool:
            raise RuntimeError(
                f"Argument of BoolUtil.serialize has type {TypeUtil.name(value)} while only bool is accepted."
            )
        return "true" if value else "false"

    @classmethod
    def parse(cls, value: str | None, *, name: str | None = None) -> bool:
        """Parse an optional boolean value, param 'name' is used for error reporting only."""
        match value:
            case None | "":
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f"for field {name}" if name else "for a true/false field"
                raise UserError(f"The value {for_field} is empty. Valid values are lowercase 'true' or 'false'.")
            case "true":
                return True
            case "false":
                return False
            case _:
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f"for field {name}" if name is not None else "for a true/false field"
                raise UserError(f"The value {for_field} must be lowercase 'true' or 'false'.\n"
                                f"Field value: {value}")

    @classmethod
    def parse_or_none(cls, value: str | None, *, name: str | None = None) -> bool | None:
        """Parse an optional boolean value, param 'name' is used for error reporting only."""
        match value:
            case None | "":
                return None
            case "true":
                return True
            case "false":
                return False
            case _:
                name = CaseUtil.snake_to_pascal_case(name)
                for_field = f"for field {name}" if name is not None else "for a true/false field"
                raise UserError(f"The value {for_field} must be lowercase 'true', 'false', or an empty string.\n"
                                f"Field value: {value}")
