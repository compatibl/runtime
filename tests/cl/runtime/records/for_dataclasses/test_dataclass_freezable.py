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
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey

FROZEN_MESSAGE_SUBSTR = "because the instance is frozen"
TUPLE_MESSAGE_SUBSTR = "'tuple' object does not support item assignment"
NON_FREEZABLE_MESSAGE_SUBSTR = "does not support DataProtocol"


def test_simple_fields():
    """Test for freezing of data inside simple fields."""

    # Attempt to modify field after freezing
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassRecord().build()
        record.id = "xyz"


def test_nested_fields():
    """Test for freezing of data inside nested fields."""

    # Attempt to set fields after freezing
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassNestedFields().build()
        record.derived_from_derived_field.int_field = 456
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassNestedFields().build()
        record.key_field = StubDataclassRecordKey(id="abc")


def test_container_fields():
    """Test for freezing of data inside containers."""

    # Building before freezing
    StubDataclassListDictFields(float_list_dict={"a": [1.23]}).build()

    # Attempt to set fields after freezing
    with pytest.raises(TypeError, match=TUPLE_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields(float_list_dict={"a": [1.23]}).build()
        record.float_list_dict["a"][0] = 4.56
    with pytest.raises(RuntimeError, match=FROZEN_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields(float_list_dict={"a": [1.23]}).build()
        record.record_list_dict["a"][0].id = "xyz"
    with pytest.raises(TypeError, match=TUPLE_MESSAGE_SUBSTR):
        record = StubDataclassListDictFields(float_list_dict={"a": [1.23]}).build()
        record.record_list_dict["a"][0] = StubDataclassRecord(id="xyz")


def test_freeze():
    """Test for freeze."""

    # Try freezing freezable objects
    record = StubDataclassRecord()
    record.build()
    assert record.is_frozen()

    nested_fields = StubDataclassNestedFields()
    nested_fields.build()
    assert nested_fields.is_frozen()


def test_refreeze():
    """Test calling build or freeze more than once."""

    # Call build twice
    record = StubDataclassRecord()
    record = record.build()
    record.build()


if __name__ == "__main__":
    pytest.main([__file__])
