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

import os
from _pytest.fixtures import FixtureRequest
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil


class PytestUtil:
    """Helper methods for pytest, depends on pytest package."""

    @classmethod
    def get_env_dir(cls, request: FixtureRequest) -> str:
        """
        Return module_dir/test_module/test_function or module_dir/test_module/test_class/test_method
        using the data from FixtureRequest, collapsing levels with identical name into one.
        """
        return cls._get_test_env_dir_or_name(request, is_name=False)

    @classmethod
    def get_env_name(cls, request: FixtureRequest) -> str:
        """
        Return module_dir/test_module.test_function or module_dir/test_module.test_class.test_method
        using the data from FixtureRequest, collapsing levels with identical name into one.
        """
        return cls._get_test_env_dir_or_name(request, is_name=True)

    @classmethod
    def _get_test_env_dir_or_name(cls, request: FixtureRequest, *, is_name: bool) -> str:
        """
        Return test_module<delim>test_function or test_module<delim>test_class<delim>test_function
        using the data from FixtureRequest, collapsing levels with identical name into one,
        where <delim> is period when is_name is True and os.sep when is_name is False.
        """
        module_file = str(request.path)
        test_name = request.node.name
        class_name = TypeUtil.name(request.cls) if request.cls is not None else None

        if module_file.endswith(".py"):
            module_file_without_ext = module_file.removesuffix(".py")
        else:
            raise RuntimeError(f"Test module file {module_file} does not end with '.py'.")

        # Determine delimiter based on is_name flag
        delim = "." if is_name else os.sep

        module_dir = os.path.dirname(module_file_without_ext)
        module_name = os.path.basename(module_file_without_ext)
        if class_name is None:
            # Remove repeated identical tokens to shorten the path
            if module_name != test_name:
                result = delim.join((module_name, test_name))
            else:
                result = module_name
        else:
            # Convert class name to snake_case
            class_name = CaseUtil.pascal_to_snake_case(class_name)

            # Remove repeated identical tokens to shorten the path
            if module_name != class_name:
                if class_name != test_name:
                    result = delim.join((module_name, class_name, test_name))
                else:
                    result = delim.join((module_name, class_name))
            else:
                if module_name != test_name:
                    result = delim.join((module_name, test_name))
                else:
                    result = module_name
        if not is_name:
            result = os.path.join(module_dir, result)
        return result
