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
from cl.runtime.storage.dataset_util import DatasetUtil


def test_to_levels():
    """Test conversion of dataset string to levels."""

    assert DatasetUtil.to_levels(None) == []
    assert DatasetUtil.to_levels("\\") == []
    assert DatasetUtil.to_levels("\\A") == ["A"]
    assert DatasetUtil.to_levels("\\A\\B") == ["A", "B"]

    with pytest.raises(Exception):
        assert DatasetUtil.to_levels(" ")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels(" A")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels("A ")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels(" A\\B")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels("\\A\\B ")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels("\\A \\B")
    with pytest.raises(Exception):
        assert DatasetUtil.to_levels("\\A\\ B")
    with pytest.raises(Exception):
        DatasetUtil.to_levels("A")
    with pytest.raises(Exception):
        DatasetUtil.to_levels("\\A\\")
    with pytest.raises(Exception):
        DatasetUtil.to_levels("\\A\\")
    with pytest.raises(Exception):
        DatasetUtil.to_levels("\\ A")
    with pytest.raises(Exception):
        DatasetUtil.to_levels("\\A \\B")


def test_to_str():
    """Test DasetUtil.to_str()."""

    assert DatasetUtil.to_str(None) == "\\"
    assert DatasetUtil.to_str([]) == "\\"
    assert DatasetUtil.to_str(["A"]) == "\\A"
    assert DatasetUtil.to_str(["A", "B"]) == "\\A\\B"

    with pytest.raises(Exception):
        DatasetUtil.to_str(["\\\\"])
    with pytest.raises(Exception):
        DatasetUtil.to_str([" "])
    with pytest.raises(Exception):
        DatasetUtil.to_str([" A"])
    with pytest.raises(Exception):
        DatasetUtil.to_str(["A "])
    with pytest.raises(Exception):
        DatasetUtil.to_str(["\\A", "B"])
    with pytest.raises(Exception):
        DatasetUtil.to_str(["A", "B\\"])
    with pytest.raises(Exception):
        DatasetUtil.to_str(["A", "\\B"])
    with pytest.raises(Exception):
        DatasetUtil.to_str(["A\\", "B"])


def test_combine():
    """Test DatasetUtil.combine."""

    assert DatasetUtil.combine(None) == []
    assert DatasetUtil.combine("\\") == []
    assert DatasetUtil.combine(None, None) == []
    assert DatasetUtil.combine("\\", None) == []
    assert DatasetUtil.combine(None, "\\A") == ["A"]
    assert DatasetUtil.combine("\\A", None) == ["A"]
    assert DatasetUtil.combine("\\A") == ["A"]
    assert DatasetUtil.combine("\\A", "\\B") == ["A", "B"]
    assert DatasetUtil.combine(None, ["A"], ["B"]) == ["A", "B"]

    with pytest.raises(Exception):
        DatasetUtil.combine("\\\\")
    with pytest.raises(Exception):
        DatasetUtil.combine(" ")
    with pytest.raises(Exception):
        DatasetUtil.combine(" A")
    with pytest.raises(Exception):
        DatasetUtil.combine("A ")
    with pytest.raises(Exception):
        DatasetUtil.combine("\\A", "B")
    with pytest.raises(Exception):
        DatasetUtil.combine("A", "B\\")
    with pytest.raises(Exception):
        DatasetUtil.combine("A", "\\B")
    with pytest.raises(Exception):
        DatasetUtil.combine("A\\", "B")


def test_lookup_list():
    """Test DatasetUtil.to_lookup_list."""

    assert DatasetUtil.to_lookup_list(None) == ["\\"]
    assert DatasetUtil.to_lookup_list("\\") == ["\\"]
    assert DatasetUtil.to_lookup_list("\\A") == ["\\A", "\\"]
    assert DatasetUtil.to_lookup_list("\\A\\B") == ["\\A\\B", "\\A", "\\"]


if __name__ == "__main__":
    pytest.main([__file__])
