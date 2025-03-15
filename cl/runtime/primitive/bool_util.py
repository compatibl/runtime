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
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil


class BoolUtil:
    """Helper methods for working with bool type."""

    NONE_VALUES = (None, "", "null")
    """Values that are considered None when deserializing."""

    @classmethod
    def to_str(cls, value: bool) -> str:
        """Serialize True as lowercase 'true' and False as 'false', error if argument is None."""
        if value.__class__ is bool:
            return "true" if value else "false"
        elif value is None:
            raise ErrorUtil.param_none_error(
                callable_name="BoolUtil.to_str",
                details="Use BoolUtil.to_str_or_none instead.",
            )
        else:
            raise ErrorUtil.param_type_error(value, callable_name="BoolUtil.to_str")

    @classmethod
    def to_str_or_none(cls, value: bool | None) -> str | None:
        """Serialize True as lowercase 'true' and False as 'false', return None if argument is None."""
        if value.__class__ is bool:
            return "true" if value else "false"
        elif value is None:
            return None
        else:
            raise ErrorUtil.param_type_error(value, callable_name="BoolUtil.to_str")

    @classmethod
    def from_str(cls, value: str) -> bool:
        """Deserialize lowercase 'true' as True and 'false' as False, error if argument is None."""
        if value is None or value.__class__ is str:
            if value == "true":
                return True
            elif value == "false":
                return False
            else:
                raise ErrorUtil.param_value_error(
                    value,
                    callable_name="BoolUtil.from_str",
                    details="Valid values are lowercase 'true' for True and 'false' for False.",
                )
        else:
            raise ErrorUtil.param_type_error(value, callable_name="BoolUtil.from_str")

    @classmethod
    def from_str_or_none(cls, value: str | None, *, name: str | None = None) -> bool | None:
        """Deserialize lowercase 'true' as True and 'false' as False, return None if argument in NONE_VALUES."""
        if value is None or value.__class__ is str:
            if value == "true":
                return True
            elif value == "false":
                return False
            elif value in cls.NONE_VALUES:
                return None
            else:
                raise ErrorUtil.param_value_error(
                    value,
                    callable_name="BoolUtil.from_str",
                    details=f"Valid values are lowercase 'true' for True, 'false' for False,\n"
                            f"and None, empty string, or 'null' for None.",
                )
        else:
            raise ErrorUtil.param_type_error(value, callable_name="BoolUtil.from_str")
