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

from cl.runtime.csv_util import CsvUtil


def test_should_wrap():
    """Test for the method to determine which CSV fields should be wrapped."""

    # Negative test cases: should NOT be wrapped
    negative_cases = [
        '"""[Begins from bracket, already wrapped',
        '"""{Begins from brace, already wrapped',
        '"""123"""',
        "[Begins from bracket",
        "{Begins from brace",
        "Hello, world!",
        "",
        "Not a date 123abc",
        "prefix March 5, 2022",
        "prefix 3.14",
        "prefix 99%",
        "1m",
    ]

    # Positive test cases: should be wrapped
    positive_cases = [
        "42",
        "3.14",
        "99%",
        "99.0%",
        "$1",
        "2023-05-21",
        "March 5, 2022"
    ]

    for case in negative_cases:
        assert not CsvUtil.should_wrap(case), f"Expected should_wrap to return False for: {case}"

    for case in positive_cases:
        assert CsvUtil.should_wrap(case), f"Expected should_wrap to return True for: {case}"
        assert CsvUtil.should_wrap('"' + case), f'Expected should_wrap to return True for: "{case}'
        assert CsvUtil.should_wrap('""' + case), f'Expected should_wrap to return True for: ""{case}'


if __name__ == "__main__":
    pytest.main([__file__])
