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

import pytest
import os
from typing import Any
from typing import Iterable
from _pytest.fixtures import FixtureRequest
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.protocols import MAPPING_CLASSES
from cl.runtime.records.protocols import SEQUENCE_CLASSES
from cl.runtime.records.type_util import TypeUtil


class PytestUtil:
    """Helper methods for pytest, depends on pytest package."""

    @classmethod
    def approx(cls, data: Any, *, abs_tol=1e-6, rel_tol=1e-6):
        """Recursively apply pytest.approx to all floats in a nested structure."""
        if isinstance(data, float):
            # Apply rounding to float values
            return pytest.approx(data, abs=abs_tol, rel=rel_tol)
        elif isinstance(data, SEQUENCE_CLASSES):
            # Recreate the same sequence type with pytest.approx for float
            sequence_type = data.__class__
            return sequence_type(cls.approx(item, abs_tol=abs_tol, rel_tol=rel_tol) for item in data)
        elif isinstance(data, MAPPING_CLASSES):
            # Recreate the same mapping type with pytest.approx for float
            mapping_type = data.__class__
            return mapping_type(
                (key, cls.approx(value, abs_tol=abs_tol, rel_tol=rel_tol)) for key, value in data.items()
            )
        return data

    @classmethod
    def get_test_dir(cls, request: FixtureRequest) -> str:
        """
        Return module_dir/test_module/test_function or module_dir/test_module/test_class/test_method
        using the data from FixtureRequest, collapsing levels with identical name into one.
        """
        return cls._get_test_dir_or_name(request, is_name=False)

    @classmethod
    def get_test_name(cls, request: FixtureRequest) -> str:
        """
        Return module_dir/test_module.test_function or module_dir/test_module.test_class.test_method
        using the data from FixtureRequest, collapsing levels with identical name into one.
        """
        return cls._get_test_dir_or_name(request, is_name=True)

    @classmethod
    def _get_test_dir_or_name(cls, request: FixtureRequest, *, is_name: bool) -> str:
        """
        Return test_module<delim>test_function or test_module<delim>test_class<delim>test_function
        using the data from FixtureRequest, collapsing levels with identical name into one,
        where <delim> is period when is_name is True and os.sep when is_name is False.
        """

        # Get test information from the request, call stack inspection like in QaUtil
        # will not work here because this code is executed before the test function
        test_file = str(request.path)
        test_name = request.node.name
        class_name = TypeUtil.name(request.cls) if request.cls is not None else None

        # Convert to test path or name
        return QaUtil.get_test_dir_or_name(
            test_file=test_file,
            class_name=class_name,
            test_name=test_name,
            is_name=is_name,
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
