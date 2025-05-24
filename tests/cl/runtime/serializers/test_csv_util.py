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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa
from cl.runtime.csv_util import CsvUtil


def test_required_quotes():
    """Test CsvUtil.required_quotes() method."""

    # Should not be wrapped
    zero_quote_cases = [
        '"""[Begins from bracket and already wrapped in 3"""',
        '"""{Begins from brace and already wrapped in 3"""',
        '"[Begins from bracket and already wrapped in 1"',
        '"{Begins from brace and already wrapped in 1"',
        "[Begins from bracket",
        "{Begins from brace",
        "",
        "Not a date 123abc",
        "prefix 05/01/2023",
        "prefix 3.14",
        "prefix 99%",
        "1m",
    ]

    # Should be wrapped in 1
    one_quote_cases = [
        "Hello, world!",  # Comma
        'Hello"world!',  # Quote
        "Hello\nworld!",  # \n
        "Hello\rworld!",  # \r
        "prefix May 1, 2003",  # Not a pure date but has comma
        '"""Trial: 0\nDec 31, 2020"""',  # Not a pure date but has \n
    ]

    # Should be wrapped in 3
    three_quote_cases = [
        "42",
        "3.14",
        "99%",
        "99.0%",
        "$1",
        "2023-05-21",
        "May 1, 2003"
    ]

    for case in zero_quote_cases:
        assert CsvUtil.required_quotes(case) == 0, f"Expected num_quotes to return 0 for: {case}"

    for case in one_quote_cases:
        assert CsvUtil.required_quotes(case) == 1, f"Expected num_quotes to return 1 for: {case}"

    for case in three_quote_cases:
        assert CsvUtil.required_quotes(case) == 3, f"Expected num_quotes to return 3 for: {case}"


def test_check_or_fix_file(pytest_work_dir):
    """Test CsvUtil.check_or_fix_file() method."""

    assert CsvUtil.check_or_fix_file("valid.csv", apply_fix=False)
    assert not CsvUtil.check_or_fix_file("unescaped_date.csv", apply_fix=False)
    assert not CsvUtil.check_or_fix_file("unescaped_float.csv", apply_fix=False)

if __name__ == "__main__":
    pytest.main([__file__])
