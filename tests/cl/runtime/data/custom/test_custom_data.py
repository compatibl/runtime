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
from stubs.cl.runtime.data.custom.stub_custom_data import StubCustomData

# Tests for Data


def test_smoke():
    """Smoke test."""

    # Create test record and populate with sample data
    obj = StubCustomData()

    # Test roundtrip serialization
    obj_dict = obj.to_dict()
    obj_clone = StubCustomData.from_dict(obj_dict)
    obj_clone_dict = obj_clone.to_dict()
    assert len(obj_dict) == 2
    assert obj_dict == obj_clone_dict


if __name__ == '__main__':
    pytest.main([__file__])