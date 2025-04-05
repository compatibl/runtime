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
from cl.runtime.records.record_util import RecordUtil
from stubs.cl.runtime import StubDataclassRecord, StubDataclassDerivedRecord, StubDataclassData, StubDataclassRecordKey


def test_get_superclasses():
    """Test getting class path from class."""

    # TODO: Add more test cases
    key_class = StubDataclassRecordKey
    base_class = StubDataclassRecord
    derived_class = StubDataclassDerivedRecord

    # Common base class, returns self and key class
    assert RecordUtil.parent_records_of(StubDataclassRecord) == (base_class, key_class)

    # Derived class, returns self, common base and key
    assert RecordUtil.parent_records_of(StubDataclassDerivedRecord) == (derived_class, base_class, key_class)

    # Invoke for a type that does not have a key class
    with pytest.raises(RuntimeError):
        RecordUtil.parent_records_of(StubDataclassData)

    # Call twice to confirm that method results are cached
    assert RecordUtil.parent_records_of(StubDataclassRecord) == (base_class, key_class)
    assert RecordUtil.parent_records_of(StubDataclassRecord) == (base_class, key_class)
    assert RecordUtil.parent_records_of.cache_info().hits > 1


if __name__ == "__main__":
    pytest.main([__file__])
