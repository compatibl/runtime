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
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerivedData
from stubs.cl.runtime import StubDataclassDerivedFromDerivedData


def test_build():
    """Test DataMixin.build method."""

    guard = RegressionGuard()
    guard.write("Testing Base:")
    StubDataclassData(_regression_guard=guard).build()
    guard.write("Testing Derived:")
    StubDataclassDerivedData(_regression_guard=guard).build()
    guard.write("Testing DerivedFromDerivedWithInit:")
    StubDataclassDerivedFromDerivedData(_regression_guard=guard).build()
    guard.verify()


def test_clone():
    """Test DataMixin.clone method."""

    # Create target from source
    guard = RegressionGuard()
    source = StubDataclassData(str_field="xyz", _regression_guard=guard)
    target = source.clone()

    # Public fields in source, only one is set
    assert target.str_field == source.str_field
    assert target.int_field == 123  # Takes its default value when not set in source

    # Protected fields in source, not set
    assert target._regression_guard is None
    guard.verify()


def test_clone_as():
    """Test DataMixin.clone_as method."""

    # Create target from source
    guard = RegressionGuard()
    source = StubDataclassData(str_field="xyz", int_field=789, _regression_guard=guard)
    target = source.clone_as(StubDataclassDerivedData)

    # Public fields in source, only one is set
    assert target.str_field == source.str_field
    assert target.int_field == source.int_field
    assert target.derived_str_field is "derived"  # Takes its default value when not present in source class

    # Protected fields in source, not set
    assert target._regression_guard is None
    guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
