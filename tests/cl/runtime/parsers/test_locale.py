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
from cl.runtime.parsers.locale import Locale


def test_init():
    """Test locale parsing into language and country."""
    test_cases = (
        ("en-US", "en", "US"),
        ("en-GB", "en", "GB"),
        ("fr-FR", "fr", "FR"),
        ("de-DE", "de", "DE"),
        ("es-ES", "es", "ES"),
        ("it-IT", "it", "IT"),
    )

    for test_case in test_cases:
        locale = Locale(locale_id=test_case[0]).init_all()
        assert locale.language == test_case[1]
        assert locale.country == test_case[2]


if __name__ == "__main__":
    pytest.main([__file__])
