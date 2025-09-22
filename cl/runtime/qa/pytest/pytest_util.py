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
from typing import Any
from typing import Iterable
from _pytest.fixtures import FixtureRequest
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.typename import typename


class PytestUtil:
    """Helper methods for pytest, depends on pytest package."""

    @classmethod
    def get_test_path_from_request(cls, request: FixtureRequest, *, name_only: bool) -> str:
        """
        Return test_module.test_function or test_module.test_class.test_method if name_only is True and
        test_dir/test_module/test_function or test_dir/test_module/test_class/test_method if name_only is False
        by inspecting the request, collapse repeated adjacent names into one.

        Args:
            request: Pytest fixture request
            name_only: If true, return only a dot delimited name, otherwise return the entire directory path
        """

        # Get test information from the request, call stack inspection like in QaUtil
        # will not work here because this code is executed before the test function
        test_file = str(request.path)
        class_name = typename(request.cls) if request.cls is not None else None  # TODO: Do not use cls as field name
        test_name_and_params = request.node.name

        # If the test is parameterized 'test_method[Params]', remove the parameters and set test_name to 'test_method'
        test_name = test_name_and_params.split("[")[0]

        # Convert to test path or name
        return QaUtil.format_test_path(
            test_file=test_file,
            test_class_name=class_name,
            test_function=test_name,
            name_only=name_only,
        )

    @classmethod
    def assert_equals_iterable_without_ordering(cls, iterable: Iterable[Any], other_iterable: Iterable[Any]) -> bool:
        """Checks that two iterables contain the same elements, regardless of order."""

        iterable_as_list = list(iterable) if not isinstance(iterable, list) else iterable
        other_iterable_as_list = list(other_iterable) if not isinstance(other_iterable, list) else other_iterable

        if len(iterable_as_list) != len(other_iterable_as_list):
            raise ValueError(
                f"Iterables have different length: {len(iterable_as_list)} and {len(other_iterable_as_list)}"
            )

        for item in iterable_as_list:
            if item not in other_iterable_as_list:
                raise ValueError(f"Item {item} contains only in first iterable.")

        return True

    @classmethod
    def log_method_info(cls, logger):
        """Log information about the caller method using stack inspection."""

        # Get logger from TaskLog
        # Record method information from stack frame
        current_frame = inspect.currentframe()
        assert current_frame is not None

        outer_frame = current_frame.f_back
        assert outer_frame is not None

        method_name = outer_frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(outer_frame)

        # Explicitly delete the frames to avoid circular references
        del outer_frame
        del current_frame

        # Log information
        params_output = ",".join(f"{arg}={values[arg]}" for arg in args)
        logger.info(f"Called {method_name}({params_output})")
