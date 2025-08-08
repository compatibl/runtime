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

import inspect
import os
from typing import Literal

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil


class QaUtil:
    """Helper methods for environment selection."""

    @classmethod
    def inspect_stack_for_test_module_patterns(cls, *, test_module_patterns: tuple[str, ...] | None = None) -> bool:
        """
        Return True if invoked from a test, detection is based on test module pattern.

        Args:
            test_module_patterns: Glob patterns to identify a running test, defaults to test_* and conftest
        """

        if test_module_patterns is not None:
            # TODO: test_module_patterns custom patterns
            raise RuntimeError("Custom test module patterns are not yet supported.")
        test_module_patterns = ("test_", "conftest")

        stack = inspect.stack()
        for frame_info in stack:
            filename = os.path.basename(frame_info.filename)
            if filename.startswith(test_module_patterns) and filename.endswith(".py"):
                return True
        return False

    @classmethod
    def get_test_dir(
        cls,
        *,
        test_function_pattern: str | None = None,
    ) -> str:
        """
        Return module_dir/test_module/test_function or module_dir/test_module/test_class/test_method,
        collapsing levels with identical name into one.

        Notes:
            Implemented by searching the stack frame for 'test_' or a custom test function name pattern.

        Args:
            test_function_pattern: Glob pattern for function or method in stack frame, defaults to 'test_*'
        """
        result = cls.get_test_path_from_call_stack(
            format_as="dir",
            test_function_pattern=test_function_pattern,
        )

        # Error if not inside a test
        if result is None:
            raise RuntimeError("Attempting to get test dir outside a test.")

        return result

    @classmethod
    def get_test_name(
        cls,
        *,
        test_function_pattern: str | None = None,
    ) -> str:
        """
        Return test_module.test_function or test_module.test_class.test_method,
        collapsing levels with identical name into one.

        Notes:
            Implemented by searching the stack frame for 'test_' or a custom test function name pattern.

        Args:
            test_function_pattern: Glob pattern for function or method in stack frame, defaults to 'test_*'
        """

        # Get test environment if inside test
        result = cls.get_test_path_from_call_stack(
            format_as="name",
            test_function_pattern=test_function_pattern,
        )

        # Error if not inside a test
        if result is None:
            raise RuntimeError("Attempting to get test name outside a test.")

        return result

    @classmethod
    def get_test_path_from_call_stack(
        cls,
        *,
        format_as: Literal["name", "dir"],
        test_function_pattern: str | None = None,
    ) -> str | None:
        """
        Return test_module<delim>test_function or test_module<delim>test_class<delim>test_function
        by searching the call stack for test_function_pattern and collapsing levels with identical name into one,
        where <delim> is period when is_name is True and os.sep when is_name is False.

        Notes:
            Implemented by searching the stack frame for 'test_' or a custom test function name pattern.

        Args:
            is_name: If True, return dot delimited name, otherwise return directory path
            test_function_pattern: Glob pattern for function or method in stack frame, defaults to 'test_*'
        """

        if test_function_pattern is not None:
            # TODO: Support custom patterns
            raise RuntimeError("Custom test function or method name patterns are not yet supported.")
        test_function_pattern = "test_"

        stack = inspect.stack()
        for frame_info in stack:
            if frame_info.function.startswith(test_function_pattern):

                # Get test information from the call stack
                frame_globals = frame_info.frame.f_globals
                test_file = frame_globals["__file__"]
                test_name = frame_info.function
                cls_instance = frame_info.frame.f_locals.get("self", None)
                class_name = TypeUtil.name(cls_instance) if cls_instance else None

                # Convert to test path or name
                return cls.get_test_path(
                    test_file=test_file,
                    test_class=class_name,
                    test_function=test_name,
                    format_as=format_as,
                )

        # Not inside test, return None
        return None

    @classmethod
    def get_test_path(
        cls,
        *,
        test_file: str,
        test_class: str | None = None,
        test_function: str,
        format_as: Literal["name", "dir"],
    ) -> str | None:
        """
        Return test name test_module.test_function or test_module.test_class.test_method if format_as is "name" and
        test_dir/test_module/test_function or test_dir/test_module/test_class/test_method if format_as is "dir",
        collapsing repeated adjacent names into one.

        Args:
            test_file: Test file inclusive of directory path and .py extension
            test_class: Test class name if the test is a method inside class, None otherwise
            test_function: Test function or method name
            format_as: If "name", return dot delimited name, if "dir", return directory path
        """

        if test_file.endswith(".py"):
            test_file_without_ext = test_file.removesuffix(".py")
        else:
            raise RuntimeError(f"Test file path {test_file} does not end with '.py'.")

        # Determine delimiter based on format_as parameter
        if format_as == "name":
            is_dir = False
            delim = "."
        elif format_as == "dir":
            is_dir = True
            delim = os.sep
        else:
            raise RuntimeError(f"Parameter format_as={format_as} is not supported, valid values are 'name' and 'dir'.")

        module_dir = os.path.dirname(test_file_without_ext)
        module_name = os.path.basename(test_file_without_ext)
        if test_class is None:
            # Remove repeated identical tokens to shorten the path
            if module_name != test_function:
                result = delim.join((module_name, test_function))
            else:
                result = module_name
        else:
            # Convert class name to snake_case
            test_class = CaseUtil.pascal_to_snake_case(test_class)

            # Remove repeated identical tokens to shorten the path
            if module_name != test_class:
                if test_class != test_function:
                    result = delim.join((module_name, test_class, test_function))
                else:
                    result = delim.join((module_name, test_class))
            else:
                if module_name != test_function:
                    result = delim.join((module_name, test_function))
                else:
                    result = module_name

        if is_dir:
            # Concatenate with the directory where the test is located if format_as is "dir"
            result = os.path.join(module_dir, result)
        return result
