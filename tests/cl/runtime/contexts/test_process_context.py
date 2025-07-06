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
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.settings.app_settings import AppSettings

app_settings = AppSettings.instance()


def test_process_context():
    """Smoke test."""

    assert ProcessContext.is_testing() == True
    with ProcessContext().build() as context:
        assert context.get_env_name() == "test_process_context"


if __name__ == "__main__":
    pytest.main([__file__])
