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
from cl.runtime.records.key_util import KeyUtil
from stubs.cl.runtime import StubDataclassKey


def test_get_hash():
    """Test KeyMixin.get_hash method."""

    sample_a = StubDataclassKey(id="a").build()
    sample_b = StubDataclassKey(id="b").build()
    sample_set_a = {KeyUtil.get_hash(sample_a), KeyUtil.get_hash(sample_a)}
    assert len(sample_set_a) == 1

    sample_set_b = {KeyUtil.get_hash(sample_a), KeyUtil.get_hash(sample_b)}
    assert len(sample_set_b) == 2

    with pytest.raises(Exception, match="not frozen"):
        # Not frozen
        KeyUtil.get_hash(StubDataclassKey(id="a"))


if __name__ == "__main__":
    pytest.main([__file__])
