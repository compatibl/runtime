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
from stubs.cl.runtime.data.attrs.stub_attrs_simple_record_key import StubAttrsSimpleRecordKey


def test_smoke():
    """Smoke test."""

    # Create test base_record and populate with sample data
    key = StubAttrsSimpleRecordKey(key_field_str="abc", key_field_int=123)

    # Test type and key
    table_name = key.get_table()
    assert table_name == f"{type(key).__module__}.{type(key).__name__}"
    assert key.get_key() == 'abc;123'

    # Test roundtrip serialization
    key_dict = key.to_dict()
    key_clone = StubAttrsSimpleRecordKey.from_dict(key_dict)
    key_clone_dict = key_clone.to_dict()
    assert len(key_dict) == 2
    assert key_dict == key_clone_dict


if __name__ == '__main__':
    pytest.main([__file__])