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
from cl.runtime.testing.unit_test_context import UnitTestContext


def test_smoke():
    """Test get_base_path in a test function."""

    with UnitTestContext() as context:
        assert context.context_id == "test_unit_test_context.test_smoke"
        assert context.data_source.data_source_id == context.context_id


if __name__ == "__main__":
    pytest.main([__file__])