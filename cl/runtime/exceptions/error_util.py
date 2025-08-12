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

from enum import Enum
from textwrap import TextWrapper
from typing import Any
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.type_util import TypeUtil


class ErrorUtil:
    """Helper class for creating exception objects with detailed error messages."""

    _wrapper: TextWrapper = TextWrapper(
        width=70,
        max_lines=10,
        initial_indent=" " * 4,
        subsequent_indent=" " * 4,
    )

    @classmethod
    def param_none_error(
        cls,
        *,
        details: str | None = None,
        callable_name: str | None = None,
        param_name: str | None = None,
    ) -> Exception:
        """
        Return exception instance stating that callable does not accept parameted value None.

        Args:
            details: Further details about the error in single- or multi-line sentence format (optional)
            callable_name: Function name in snake_case format or method name in ClassName.method_name format (optional)
            param_name: Snake case parameter name (optional)
        """
        details_str = cls.wrap(details) if details else ""
        callable_str = f"Method {callable_name}" if "." in callable_name else f"Function {callable_name}"
        param_value_str = f"None for parameter '{param_name}'" if param_name else "None"
        return RuntimeError(f"{callable_str} does not accept {param_value_str}.\n{details_str}")

    @classmethod
    def param_type_error(
        cls,
        value: Any,
        *,
        details: str | None = None,
        callable_name: str | None = None,
        param_name: str | None = None,
    ) -> Exception:
        """
        Return exception instance stating that callable does not accept parameter type.

        Args:
            details: Further details about the error in single- or multi-line sentence format (optional)
            value: Parameter value that caused the error
            callable_name: Function name in snake_case format or method name in ClassName.method_name format (optional)
            param_name: Snake case parameter name (optional)
        """
        type_str = TypeUtil.name(value)
        details_str = cls.wrap(details) if details else ""
        callable_str = f"Method {callable_name}" if "." in callable_name else f"Function {callable_name}"
        param_str = f"type {type_str} for parameter '{param_name}'" if param_name else f"parameter type {type_str}"
        return RuntimeError(
            f"{callable_str} does not accept {param_str}.\n{details_str}" f"Parameter value: {cls.wrap(value)}"
        )

    @classmethod
    def param_value_error(
        cls,
        value: Any,
        *,
        details: str | None = None,
        callable_name: str | None = None,
        param_name: str | None = None,
    ) -> Exception:
        """
        Return exception instance stating that callable does not accept the input.

        Args:
            details: Further details about the error in single- or multi-line sentence format (optional)
            value: Parameter value that caused the error
            callable_name: Function name in snake_case format or method name in ClassName.method_name format (optional)
            param_name: Snake case parameter name (optional)
        """
        details_str = cls.wrap(details) if details else ""
        callable_str = f"Method {callable_name}" if "." in callable_name else f"Function {callable_name}"
        param_str = f"parameter '{param_name}'" if param_name else "parameter"
        return RuntimeError(
            f"Invalid value for {callable_str} {param_str}.\n{details_str}" f"\nParameter value: {cls.wrap(value)}"
        )

    @classmethod
    def enum_value_error(cls, value: Enum | str, schema_type: type | str | None = None) -> Exception:
        """Error message on unknown format enum."""
        schema_type = schema_type if isinstance(schema_type, str) else TypeUtil.name(schema_type)
        if value is None:
            type_str = f"the enum type {schema_type}" if schema_type is not None else "an enum type"
            return RuntimeError(f"Value of None is passed for {type_str}.")
        else:
            # Check that schema type matches if specified
            if schema_type is not None and schema_type != (value_type_name := TypeUtil.name(type(value))):
                return RuntimeError(
                    f"Type {value_type_name} of enum value does not match the type in schema {schema_type}"
                )
            else:
                enum_type_name = TypeUtil.name(value)
                enum_value_str = value.name if isinstance(value, Enum) else str(value)
                valid_items = "\n".join(item.name for item in value.__class__)
                return RuntimeError(
                    f"Enum {enum_type_name} does not include the item {enum_value_str}.\n"
                    f"Valid items are:\n{valid_items}\n"
                )

    @classmethod
    def mutually_exclusive_fields_error(
        cls,
        fields: list[str],
        *,
        class_name: str,
        details: str | None = None,
    ) -> Exception:
        """
        Return exception instance stating that the specified fields are mutually exclusive
        for the specified type.

        Args:
            fields: List of field names that are mutually exclusive
            details: Further details about the error in single- or multi-line sentence format (optional)
            class_name: Class name for which the error is reported
        """
        fields_str = ", ".join(fields)
        details_str = cls.wrap(details) if details else ""
        return RuntimeError(f"Fields {fields_str} are mutually exclusive for type {class_name}.\n{details_str}")

    @classmethod
    def mutually_required_fields_error(
        cls,
        fields: list[str],
        *,
        class_name: str,
        details: str | None = None,
    ) -> Exception:
        """
        Return exception instance stating that the specified fields should be specified together or not at all
        for the specified type.

        Args:
            fields: List of field names that must be specified together
            details: Further details about the error in single- or multi-line sentence format (optional)
            class_name: Class name for which the error is reported
        """
        fields_str = ", ".join(fields)
        details_str = cls.wrap(details) if details else ""
        return RuntimeError(
            f"Fields {fields_str} for type {class_name}\n"
            f"must be specified together or not not at all.\n"
            f"{details_str}"
        )

    @classmethod
    def value_error(
        cls,
        value: Any,
        details: str | None = None,
        *,
        value_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
    ) -> Exception:
        """
        Return "The value '{value}' of {description} caused an error."

        Args:
            value: The value for which the error is reported
            details: Further details about the error in single- or multi-line sentence format (optional)
            value_name: Variable, field or parameter name for formatting the error message (optional)
            method_name: Method or function name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
        """
        if method_name is not None:
            of_what = cls._of_param(param_name=value_name, method_name=method_name, data_type=data_type)
        elif data_type is not None:
            of_what = cls._of_field(field_name=value_name, data_type=data_type)
        elif value_name is not None:
            if CaseUtil.is_snake_case(value_name):
                value_name = CaseUtil.snake_to_pascal_case(value_name)
            of_what = f"of {value_name} "
        else:
            of_what = ""

        if StringUtil.is_not_empty(details):
            details_msg = f"\nFurther details:\n\n{details.strip()}\n"
        else:
            details_msg = ""

        if value is not None:
            error_msg = f"The following value {of_what}caused an error:\n\n{str(value)}\n{details_msg}"
        else:
            error_msg = f"An empty value {of_what}caused an error.\n{details_msg}"
        return UserError(error_msg)

    @classmethod
    def _of_field(
        cls,
        *,
        field_name: str | None = None,
        data_type: type | str | None = None,
    ) -> str:
        """
        Return "of field {description}" or the empty string if parameters are None.

        Args:
            field_name: Parameter or field name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
        """
        # Convert field name
        if not StringUtil.is_empty(field_name):
            if CaseUtil.is_snake_case(field_name):
                field_name = CaseUtil.snake_to_pascal_case(field_name)
            field_str = f"of field {field_name} "
        elif data_type is not None:
            field_str = "of a field "
        else:
            field_str = ""

        # Convert type
        if data_type is not None:
            data_type = data_type.__name__ if isinstance(data_type, type) else str(data_type)
        if not StringUtil.is_empty(data_type):
            record_str = f"in {data_type} "
        else:
            record_str = ""

        # Create the message
        result = f"{field_str}{record_str}"
        return result

    @classmethod
    def _of_param(
        cls,
        *,
        param_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
    ) -> str:
        """
        Return "of parameter {description}" or the empty string if parameters are None.

        Args:
            param_name: Parameter name for formatting the error message (optional)
            method_name: Method or function name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
        """
        # Convert field name
        if not StringUtil.is_empty(param_name):
            if CaseUtil.is_snake_case(param_name):
                param_name = CaseUtil.snake_to_pascal_case(param_name)
            field_str = f"of parameter {param_name} "
        elif method_name is not None:
            field_str = "of a parameter "
        else:
            return ""

        # Convert class name
        if data_type is not None:
            data_type = data_type.__name__ if isinstance(data_type, type) else str(data_type)

        # Convert method name
        if not StringUtil.is_empty(method_name):
            if CaseUtil.is_snake_case(method_name):
                method_name = CaseUtil.snake_to_pascal_case(method_name)
            if StringUtil.is_empty(data_type):
                return f"{field_str}in function {method_name} "
            else:
                return f"{field_str}in method {method_name} of {data_type} "
        else:
            return field_str

    @classmethod
    def wrap(cls, value: Any, *, ensure_eol: bool | None = None) -> str:
        """Format and add leading and training EOL to a long or multiline string, leave a single line string as is."""
        if not value:
            # Return empty string if value is None or empty
            return ""
        if not isinstance(value, str):
            # Convert to string if not yet a string
            value = str(value)
        # Long or multiline string
        if len(value) > cls._wrapper.width or "\n" in value:
            # Wrap lines, indent, and add leading and training EOL
            return f"\n{cls._wrapper.fill(value)}\n"
        else:
            # Return short string as is but ensure it ends with EOL
            return value if value.endswith("\n") else f"{value}\n"
