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
from cl.runtime.prebuild.csv_preloads import check_csv_preloads


def test_csv_preloads():
    """Prebuild test to check that CSV preloads follow the format rules."""

    # Get the list files where copyright header is missing, incorrect, or not followed by a blank line
    check_csv_preloads(apply_fix=False)


if __name__ == "__main__":
    pytest.main([__file__])
