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
from cl.runtime.settings.settings_util import SettingsUtil


def test_to_str_tuple_or_none():
    """Test SettingsUtil.to_str_tuple_or_none method."""

    assert SettingsUtil.to_str_tuple_or_none(None) is None
    assert SettingsUtil.to_str_tuple_or_none([]) is None
    assert SettingsUtil.to_str_tuple_or_none("a") == ("a",)
    assert SettingsUtil.to_str_tuple_or_none(1) == ("1",)
    assert SettingsUtil.to_str_tuple_or_none([1, 2, 3]) == ("1", "2", "3")
    assert SettingsUtil.to_str_tuple_or_none("a,b,c") == ("a", "b", "c")
    assert SettingsUtil.to_str_tuple_or_none("a, b, c") == ("a", "b", "c")
    assert SettingsUtil.to_str_tuple_or_none("[a, b, c]") == ("a", "b", "c")


def test_to_str_tuple():
    """Test SettingsUtil.to_str_tuple method."""

    with pytest.raises(RuntimeError):
        SettingsUtil.to_str_tuple(None)
    with pytest.raises(RuntimeError):
        SettingsUtil.to_str_tuple([])


if __name__ == "__main__":
    pytest.main([__file__])
