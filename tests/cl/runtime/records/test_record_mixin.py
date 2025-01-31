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
from cl.runtime import RecordMixin
from cl.runtime.records.protocols import TKey
from cl.runtime.testing.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey


class Base(RecordMixin[StubDataclassRecord], StubDataclassRecordKey):
    """Test class."""

    def get_key(self) -> TKey:
        raise NotImplementedError()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> Base.init")


class Derived(Base):
    """Test class."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write(">> Derived.init")


class DerivedFromDerivedWithInit(Derived):
    """Test class."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write(">>> DerivedFromDerivedWithInit.init")


class DerivedFromDerivedWithoutInit(Derived):
    """Test class."""


class _OneLeadingUnderscore(RecordMixin[StubDataclassRecord], StubDataclassRecordKey):
    """Test class."""

    def get_key(self) -> TKey:
        raise NotImplementedError()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> _OneLeadingUnderscore.init")


class __TwoLeadingUnderscores(RecordMixin[StubDataclassRecord], StubDataclassRecordKey):
    """Test class."""

    def get_key(self) -> TKey:
        raise NotImplementedError()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> __TwoLeadingUnderscores.init")


def test_build():
    """Test RecordUtil.init_all method."""

    guard = RegressionGuard()
    guard.write("Testing Base:")
    Base().build()
    guard.write("Testing Derived:")
    Derived().build()
    guard.write("Testing DerivedFromDerivedWithInit:")
    DerivedFromDerivedWithInit().build()
    guard.write("Testing DerivedFromDerivedWithoutInit:")
    DerivedFromDerivedWithoutInit().build()
    guard.write("Testing _OneLeadingUnderscore:")
    _OneLeadingUnderscore().build()
    guard.write("Testing __TwoLeadingUnderscores:")
    __TwoLeadingUnderscores().build()
    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
