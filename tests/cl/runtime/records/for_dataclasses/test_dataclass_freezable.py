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

from cl.runtime.records.build_what_enum import BuildWhatEnum
from cl.runtime.records.for_dataclasses.freezable_util import FreezableUtil
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_complex_freezable import StubDataclassComplexFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_freezable import StubDataclassListFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_non_freezable import StubDataclassNonFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_partial_freezable import StubDataclassPartialFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_simple_freezable import StubDataclassSimpleFreezable


def test_simple_freezable():
    """Test for StubDataclassSimpleFreezable."""

    # Create and modify field before freezing
    record = StubDataclassSimpleFreezable()
    record.value = "def"

    # Freeze record
    record.build()

    # Attempt to modify field after freezing
    with pytest.raises(AttributeError):
        record.value = "xyz"


def test_complex_freezable():
    """Test for StubDataclassComplexFreezable."""

    # Create and modify field before freezing
    record = StubDataclassComplexFreezable()
    record.value = "def"

    # Freeze record
    record.build()

    # Attempt to set fields after freezing
    with pytest.raises(AttributeError):
        record.value = "xyz"
    with pytest.raises(AttributeError):
        record.freezable_obj = StubDataclassSimpleFreezable()
    with pytest.raises(AttributeError):
        record.freezable_tuple = (StubDataclassSimpleFreezable(),)

    # Attempt to modify freezable fields after freezing
    with pytest.raises(Exception):
        record.freezable_obj.value = "xyz"
    with pytest.raises(Exception):
        record.freezable_tuple[1].value = "xyz"


@pytest.mark.skip("Turn back on when build requires freezable.")  # TODO: Turn back on when build requires freezable
def test_incomplete_freezable():
    """Test for classes that are not completely freezable."""

    # Attempt to freeze non-freezable objects
    with pytest.raises(Exception):
        StubDataclassData().build()  # noqa
    with pytest.raises(Exception):
        StubDataclassPartialFreezable().build()
    with pytest.raises(Exception):
        StubDataclassListFreezable().build()


def test_try_freeze():
    """Test for FreezableUtil.try_freeze."""

    # Try freezing a non-freezable object
    assert not FreezableUtil.try_freeze(StubDataclassNonFreezable(), what=BuildWhatEnum.NEW)

    # Try freezing freezable objects
    assert FreezableUtil.try_freeze(StubDataclassSimpleFreezable(), what=BuildWhatEnum.NEW)
    assert FreezableUtil.try_freeze(StubDataclassComplexFreezable(), what=BuildWhatEnum.NEW)


def test_unfreeze():
    """Test for passing None to freeze method."""

    # Error when passing what=None when already frozen, but the object remains frozen
    record = StubDataclassSimpleFreezable()
    with pytest.raises(Exception):
        record.build(what=None)  # noqa

    # Error when passing what=None when unfrozen
    record = StubDataclassSimpleFreezable()
    with pytest.raises(Exception):
        record.build(what=None)  # noqa


def test_refreeze():
    """Test for passing a different value of what to freeze method."""

    # No error when trying to refreeze, but the value of what_frozen remains the same
    record = StubDataclassSimpleFreezable().build(what=BuildWhatEnum.NEW)
    record.build(what=BuildWhatEnum.DESERIALIZED)
    assert record.what_frozen() == BuildWhatEnum.NEW
    record.build(what=BuildWhatEnum.KEY)
    assert record.what_frozen() == BuildWhatEnum.NEW


if __name__ == "__main__":
    pytest.main([__file__])
