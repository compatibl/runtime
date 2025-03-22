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
from cl.runtime.records.for_dataclasses.freezable_util import FreezableUtil
from stubs.cl.runtime import StubDataclassRecord, StubDataclassNestedFields, StubDataclassRecordKey, \
    StubDataclassListDictFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_non_freezable import StubDataclassNonFreezable

FROZEN_MESSAGE_SUBSTR = "because the instance is frozen"
NON_FREEZABLE_MESSAGE_SUBSTR = "does not support DataProtocol"

def test_simple_fields():
    """Test for StubDataclassSimpleFreezable."""

    # Attempt to modify field after freezing
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassRecord().build()
        record.id = "xyz"


def test_nested_fields():
    """Test for StubDataclassComplexFreezable."""

    # Attempt to set fields after freezing
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassNestedFields().build()
        record.derived_from_derived_field.int_field = 456
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassNestedFields().build()
        record.key_field = StubDataclassRecordKey(id="abc")

@pytest.mark.skip(reason="TODO: Not yet implemented, will fix")  # TODO: Implement freezable for containers
def test_container_fields():
    """Test for StubDataclassComplexFreezable."""

    record = StubDataclassListDictFields().build()
    record.float_list_dict["a"][0] = 4.56

    # Attempt to set fields after freezing
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields().build()
        record.float_list_dict["a"][0] = 4.56
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields().build()
        record.record_list_dict["a"][0].id = "xyz"
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields().build()
        record.record_list_dict["a"][0] = StubDataclassRecord(id="xyz")


def test_try_freeze():
    """Test for FreezableUtil.try_freeze."""

    # Try freezing freezable objects
    assert FreezableUtil.try_freeze(StubDataclassRecord())
    assert FreezableUtil.try_freeze(StubDataclassNestedFields())

    # Try freezing a non-freezable object
    with pytest.raises(RuntimeError, match=NON_FREEZABLE_MESSAGE_SUBSTR):
        assert not FreezableUtil.try_freeze(StubDataclassNonFreezable())


def test_refreeze():
    """Test calling build or freeze more than once."""

    # Call build twice
    record = StubDataclassRecord()
    record = record.build()
    record.build()

    # Call freeze twice
    record = StubDataclassRecord()
    record.freeze()
    record.freeze()


if __name__ == "__main__":
    pytest.main([__file__])
