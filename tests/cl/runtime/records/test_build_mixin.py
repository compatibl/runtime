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
from dataclasses import dataclass
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.testing.regression_guard import RegressionGuard


@dataclass(slots=True, kw_only=True)
class Base(Freezable):
    _protected_base_field: str | None = None
    public_base_field_1: str | None = None
    public_base_field_2: str | None = None

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> Base.init")


@dataclass(slots=True, kw_only=True)
class Derived(Base):
    public_derived_field: str | None = None

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write(">> Derived.init")


@dataclass(slots=True, kw_only=True)
class DerivedFromDerivedWithInit(Derived):
    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write(">>> DerivedFromDerivedWithInit.init")


@dataclass(slots=True, kw_only=True)
class DerivedFromDerivedWithoutInit(Derived):
    pass


@dataclass(slots=True, kw_only=True)
class _OneLeadingUnderscore(Freezable):
    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> _OneLeadingUnderscore.init")


@dataclass(slots=True, kw_only=True)
class __TwoLeadingUnderscores(Freezable):
    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        RegressionGuard().write("> __TwoLeadingUnderscores.init")


def test_build():
    """Test BuildMixin.build method."""

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


def test_clone():
    """Test BuildMixin.clone method."""

    # Create target from source
    source = Base(public_base_field_1="public_base_field_1")
    target = source.clone()

    # Public fields in source, only one is set
    assert target.public_base_field_1 == source.public_base_field_1
    assert target.public_base_field_2 is None

    # Protected fields in source, not set
    assert target._protected_base_field is None


def test_clone_as():
    """Test BuildMixin.clone_as method."""

    # Create target from source
    source = Base(public_base_field_1="public_base_field_1")
    target = source.clone_as(Derived)

    # Public fields in source, only one is set
    assert target.public_base_field_1 == source.public_base_field_1
    assert target.public_base_field_2 is None

    # Protected fields in source, not set
    assert target._protected_base_field is None

    # Public fields in derived, not set
    assert target.public_derived_field is None


if __name__ == "__main__":
    pytest.main([__file__])
