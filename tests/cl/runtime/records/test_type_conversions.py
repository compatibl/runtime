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
from frozendict import frozendict
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.type_conversions import TypeConversions
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassData
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey

_KEY_INSTANCE = StubDataclassKey().build()
_KEY_SEQUENCE = (StubDataclassKey().build(), StubDataclassKey().build())
_KEY_INSTANCE_NOT_FROZEN = StubDataclassKey()
_RECORD_INSTANCE = StubDataclass().build()
_RECORD_SEQUENCE = (StubDataclass().build(), StubDataclass().build())
_RECORD_INSTANCE_NOT_FROZEN = StubDataclass()


def test_to_key_sequence():
    """Test for to_key_sequence TypeConversions.to_key_sequence."""

    # Valid cases
    assert TypeConversions.to_key_sequence(_KEY_INSTANCE) == (_KEY_INSTANCE,)
    assert TypeConversions.to_key_sequence(_KEY_SEQUENCE) == _KEY_SEQUENCE

    # Invalid cases
    with pytest.raises(Exception):
        # Not frozen
        TypeConversions.to_key_sequence(_KEY_INSTANCE_NOT_FROZEN)
    with pytest.raises(Exception):
        TypeConversions.to_key_sequence(_RECORD_INSTANCE)
    with pytest.raises(Exception):
        TypeConversions.to_key_sequence(_RECORD_SEQUENCE)
    with pytest.raises(Exception):
        TypeConversions.to_key_sequence(123)
    with pytest.raises(Exception):
        # Instance rather than type
        TypeConversions.to_key_sequence(StubDataclassKey)


def test_to_record_sequence():
    """Test for to_record_sequence TypeConversions.to_record_sequence."""

    # Valid cases
    assert TypeConversions.to_record_sequence(_RECORD_INSTANCE) == (_RECORD_INSTANCE,)
    assert TypeConversions.to_record_sequence(_RECORD_SEQUENCE) == _RECORD_SEQUENCE

    # Invalid cases
    with pytest.raises(Exception):
        # Not frozen
        TypeConversions.to_record_sequence(_RECORD_INSTANCE_NOT_FROZEN)
    with pytest.raises(Exception):
        TypeConversions.to_record_sequence(_KEY_INSTANCE)
    with pytest.raises(Exception):
        TypeConversions.to_record_sequence(_KEY_SEQUENCE)
    with pytest.raises(Exception):
        TypeConversions.to_record_sequence(123)
    with pytest.raises(Exception):
        # Instance rather than type
        TypeConversions.to_record_sequence(StubDataclassRecord)


if __name__ == "__main__":
    pytest.main([__file__])
