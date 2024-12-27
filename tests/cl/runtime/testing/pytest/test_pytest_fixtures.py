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
from cl.runtime.context.env_util import EnvUtil
from cl.runtime.testing.pytest.pytest_fixtures import testing_work_dir


def _test_working_dir(*, actual: str, expected: str):
    """Test for EnvUtil.env_dir and EnvUtil.env_name."""
    dir_name = os.path.dirname(__file__)
    expected_dir = os.path.join(dir_name, expected.replace(".", os.sep))
    assert actual == expected_dir
    assert os.getcwd() == expected_dir
    assert EnvUtil.get_env_dir() == expected_dir


class TestPytestFixtures:
    """Stub pytest class."""

    def test_pytest_fixtures(self, testing_work_dir):
        """All three names match, one-token path."""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures")

    def test_in_instance_method(self, testing_work_dir):
        """Method name does not match, two-token path"""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_in_instance_method")

    def test_in_class_method(self, testing_work_dir):
        """Method name does not match, two-token path"""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_in_class_method")


class TestClass:
    """Stub pytest class."""

    def test_pytest_fixtures(self, testing_work_dir):
        """Method name matches module name, still three-token path as they are not next to each other."""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_class.test_pytest_fixtures")

    def test_in_instance_method(self, testing_work_dir):
        """Method name does not match class name or module name, three-token path."""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_class.test_in_instance_method")

    def test_in_class_method(self, testing_work_dir):
        """Method name does not match class name or module name, three-token path."""
        _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_class.test_in_class_method")


def test_pytest_fixtures(testing_work_dir):
    """Function name matches, one-token path."""
    _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures")


def test_in_function(testing_work_dir):
    """Function name does not match, two-token path."""
    _test_working_dir(actual=testing_work_dir, expected="test_pytest_fixtures.test_in_function")


if __name__ == "__main__":
    pytest.main([__file__])
