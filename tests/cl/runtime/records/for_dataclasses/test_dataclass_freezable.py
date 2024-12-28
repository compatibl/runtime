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
from stubs.cl.runtime import StubDataclassRecordKey, StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_complex_freezable import StubDataclassComplexFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dict_fields import StubDataclassDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_simple_freezable import StubDataclassSimpleFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_list_fields import StubDataclassListFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecord


def test_simple_freezable():
    """Test for Freezable."""

    # Create and modify field before freezing
    record = StubDataclassSimpleFreezable()
    record.value = "def"

    # Freeze record
    record.freeze()

    # Attempt to modify field after freezing
    with pytest.raises(AttributeError):
        record.value = "xyz"

def test_complex_freezable():
    """Test for Freezable."""

    # Create and modify field before freezing
    record = StubDataclassComplexFreezable()
    record.value = "def"

    # Freeze record
    record.freeze()

    # Attempt to set fields after freezing
    with pytest.raises(AttributeError):
        record.value = "xyz"
    with pytest.raises(AttributeError):
        record.freezable_obj = StubDataclassSimpleFreezable()
    with pytest.raises(AttributeError):
        record.nonfreezable_obj = StubDataclassData()
    with pytest.raises(AttributeError):
        record.nonfreezable_list = [StubDataclassSimpleFreezable()]

    # Attempt to modify freezable fields after freezing
    with pytest.raises(Exception):
        record.freezable_obj.value = "xyz"

    # Attempt to modify non-freezable fields after freezing
    record.nonfreezable_obj.str_field = "xyz"
    record.nonfreezable_list.append(StubDataclassSimpleFreezable())

def test_try_freeze():
    """Test for FreezableUtil.."""
    record = StubDataclassSimpleFreezable()

    # Freeze record
    record.freeze()

    # Attempt to modify field after freezing
    with pytest.raises(AttributeError):
        record.value = "xyz"

if __name__ == "__main__":
    pytest.main([__file__])
