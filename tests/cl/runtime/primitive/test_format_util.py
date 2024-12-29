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
from typing import Callable

import pytest
import datetime as dt
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.format_util import FormatUtil

def _test_format(*, method: Callable):
    """Test the specified callable."""
    # String
    assert method("abc") == "abc"
    # Int
    assert method(123) == "123"
    assert method(-123) == "-123"
    # Float
    assert method(1.0) == "1."
    assert method(-1.23) == "-1.23"
    # Date
    assert method(dt.date(2023,4,21)) == "2023-04-21"
    # Datetime
    value = DatetimeUtil.from_fields(2023,4,21, 11, 10, 0)
    assert method(value) == "2023-04-21T11:10:00.000Z"
    value = DatetimeUtil.from_fields(2023,4,21, 11, 10, 0, millisecond=123)
    assert method(value) == "2023-04-21T11:10:00.123Z"

def test_format():
    """Test for FormatUtil.format."""
    # None or empty string
    with pytest.raises(Exception):
        FormatUtil.format(None)
    with pytest.raises(Exception):
        FormatUtil.format("")
    # Other values
    _test_format(method=FormatUtil.format)

def test_format_or_none():
    """Test for FormatUtil.format."""
    # None or empty string
    assert FormatUtil.format_or_none(None) is None
    assert FormatUtil.format_or_none("") is None
    # Other values
    _test_format(method=FormatUtil.format_or_none)


if __name__ == "__main__":
    pytest.main([__file__])
