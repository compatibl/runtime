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
from cl.runtime.qa.qa_util import QaUtil


def _test_working_dir(*, actual: str, expected: str):
    """Test for QaUtil.env_dir and QaUtil.env_name."""
    dir_name = os.path.dirname(__file__)
    expected_dir = os.path.join(dir_name, expected.replace(".", os.sep))
    assert actual == expected_dir
    assert os.getcwd() == expected_dir
    assert QaUtil.get_test_dir_from_call_stack() == expected_dir


class TestPytestFixtures:
    """Stub pytest class."""

    def test_pytest_fixtures(self, work_dir_fixture):
        """All three names match, one-token path."""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures")

    def test_in_instance_method(self, work_dir_fixture):
        """Method name does not match, two-token path"""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_in_instance_method")

    def test_in_class_method(self, work_dir_fixture):
        """Method name does not match, two-token path"""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_in_class_method")


class TestClass:
    """Stub pytest class."""

    def test_pytest_fixtures(self, work_dir_fixture):
        """Method name matches module name, still three-token path as they are not next to each other."""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_class.test_pytest_fixtures")

    def test_in_instance_method(self, work_dir_fixture):
        """Method name does not match class name or module name, three-token path."""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_class.test_in_instance_method")

    def test_in_class_method(self, work_dir_fixture):
        """Method name does not match class name or module name, three-token path."""
        _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_class.test_in_class_method")


def test_pytest_fixtures(work_dir_fixture):
    """Function name matches, one-token path."""
    _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures")


def test_in_function(work_dir_fixture):
    """Function name does not match, two-token path."""
    _test_working_dir(actual=work_dir_fixture, expected="test_pytest_fixtures.test_in_function")


if __name__ == "__main__":
    pytest.main([__file__])
