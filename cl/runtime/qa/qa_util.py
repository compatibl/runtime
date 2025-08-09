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

import fnmatch
import inspect
import os
import sys

from memoization import cached

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil


class QaUtil:
    """Helper methods for environment selection."""

    # TODO: Make it possible to modify this in QaSettings
    _test_function_pattern = "test_*"
    """Test function or method name pattern in glob format."""

    @classmethod
    @cached
    def is_test_root_process(cls) -> bool:
        """True for the root process of a test, False for the worker processes of a test or when not a test."""
        # Detect by checking if pytest is imported, will not work for other unit test frameworks (unittest, nose, etc.)
        result = "pytest" in sys.modules
        return result

    @classmethod
    def get_test_dir_from_call_stack(cls) -> str:
        """
        Return test_dir/test_module/test_function or test_dir/test_module/test_class/test_method
        collapsing repeated adjacent names into one.
        """
        result = cls.get_test_dir_from_call_stack_or_none()
        if result is None:
            # Error if not inside a test function or method
            raise RuntimeError(
                f"Attempting to get test directory from the call stack before the test function or method is called,\n"
                f"of the test function or method name does not match the pattern '{cls._test_function_pattern}'."
            )
        return result

    @classmethod
    def get_test_dir_from_call_stack_or_none(cls) -> str:
        """
        Return test_dir/test_module/test_function or test_dir/test_module/test_class/test_method
        collapsing repeated adjacent names into one.
        """
        return cls.get_test_path_from_call_stack_or_none(name_only=False)

    @classmethod
    def get_test_name_from_call_stack(cls) -> str:
        """
        Return test_module.test_function or test_module.test_class.test_method,
        collapsing repeated adjacent names into one.
        """
        result = cls.get_test_name_from_call_stack_or_none()
        if result is None:
            # Error if not inside a test function or method
            raise RuntimeError(
                f"Attempting to get test name from the call stack before the test function or method is called,\n"
                f"of the test function or method name does not match the pattern '{cls._test_function_pattern}'."
            )
        return result

    @classmethod
    def get_test_name_from_call_stack_or_none(cls) -> str | None:
        """
        Return test_module.test_function or test_module.test_class.test_method,
        collapsing repeated adjacent names into one.
        """
        return cls.get_test_path_from_call_stack_or_none(name_only=True)

    @classmethod
    def get_test_path_from_call_stack_or_none(cls, *, name_only: bool) -> str | None:
        """
        Return test_module.test_function or test_module.test_class.test_method if name_only is True and
        test_dir/test_module/test_function or test_dir/test_module/test_class/test_method if name_only is False
        by inspecting the call stack, collapse repeated adjacent names into one.

        Args:
            name_only: If true, return only a dot delimited name, otherwise return the entire directory path
        """

        stack = inspect.stack()
        for frame_info in stack:
            if fnmatch.fnmatch(frame_info.function, cls._test_function_pattern):

                # Get test information from the call stack
                frame_globals = frame_info.frame.f_globals
                test_file = frame_globals["__file__"]
                test_name = frame_info.function
                cls_instance = frame_info.frame.f_locals.get("self", None)
                class_name = TypeUtil.name(cls_instance) if cls_instance else None

                # Convert to test path or name
                return cls.format_test_path(
                    test_file=test_file,
                    test_class=class_name,
                    test_function=test_name,
                    name_only=name_only,
                )

        # Return None if not inside a test function or method
        return None

    @classmethod
    def format_test_path(
        cls,
        *,
        test_file: str,
        test_class: str | None = None,
        test_function: str,
        name_only: bool,
    ) -> str | None:
        """
        Return test_module.test_function or test_module.test_class.test_method if name_only is True and
        test_dir/test_module/test_function or test_dir/test_module/test_class/test_method if name_only is False,
        collapsing repeated adjacent names into one.

        Args:
            test_file: Test file inclusive of directory path and .py extension
            test_class: Test class name if the test is a method inside class, None otherwise
            test_function: Test function or method name
            name_only: If true, return only a dot delimited name, otherwise return the entire directory path
        """

        if test_file.endswith(".py"):
            test_file_without_ext = test_file.removesuffix(".py")
        else:
            raise RuntimeError(f"Test file path {test_file} does not end with '.py'.")

        # Determine delimiter based on format_as parameter
        if name_only:
            is_dir = False
            delim = "."
        else:
            is_dir = True
            delim = os.sep

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
