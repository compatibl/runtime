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
from cl.runtime.records.protocols import is_sequence_type
from cl.runtime.settings.qa_settings import QaSettings


def test_qa_settings():
    """Test DbSettings class."""

    qa_settings = QaSettings.instance()
    assert qa_settings.qa_db_types is not None and is_sequence_type(type(qa_settings.qa_db_types))


if __name__ == "__main__":
    pytest.main([__file__])
