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
from cl.runtime.prebuild.csv_preloads import check_csv_preloads, should_wrap


def test_should_wrap():
    """Test for the method to determine which CSV fields should be wrapped."""

    # Negative test cases: should NOT be wrapped
    negative_cases = [
        '"""[Begins from bracket, already wrapped',
        '"""{Begins from brace, already wrapped',
        '"""123"""',
        "Hello, world!",
        "",
        "Not a date 123abc",
        "prefix March 5, 2022",
        "prefix 3.14",
        "prefix 99%",
    ]

    # Positive test cases: should be wrapped
    positive_cases = [
        "[Begins from bracket",
        "{Begins from brace",
        "42",
        "3.14",
        "99%",
        "99.0%",
        "2023-05-21",
        "March 5, 2022"
    ]

    for case in negative_cases:
        assert not should_wrap(case), f"Expected should_wrap to return False for: {case}"

    for case in positive_cases:
        assert should_wrap(case), f"Expected should_wrap to return True for: {case}"
        assert should_wrap('"' + case), f'Expected should_wrap to return True for: "{case}'
        assert should_wrap('""' + case), f'Expected should_wrap to return True for: ""{case}'


def test_csv_preloads():
    """Prebuild test to check that CSV preloads follow the format rules."""

    # Get the list files where copyright header is missing, incorrect, or not followed by a blank line
    check_csv_preloads(apply_fix=False)


if __name__ == "__main__":
    pytest.main([__file__])
