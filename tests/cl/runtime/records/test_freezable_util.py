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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_non_freezable import StubDataclassNonFreezable
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_simple_freezable import StubDataclassSimpleFreezable


def test_freezable_util():
    """Test for FreezableUtil.."""

    # Try freezing a freezable object
    freezable_record = StubDataclassSimpleFreezable()
    FreezableUtil.try_freeze(freezable_record)
    assert FreezableUtil.is_frozen(freezable_record)
    assert freezable_record.is_frozen()

    # Try freezing a non-freezable object
    non_freezable_record = StubDataclassNonFreezable()
    FreezableUtil.try_freeze(non_freezable_record)
    assert not FreezableUtil.is_frozen(non_freezable_record)


if __name__ == "__main__":
    pytest.main([__file__])
