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
import logging

_LOGGER = logging.getLogger(__name__)


def test_smoke():
    """Smoke test."""

    # Get logger from TaskLog outside the outermost 'with TaskLog(...)' clause
    # Standard messages
    module_name = __name__
    _LOGGER.debug(f"Debug log message in {module_name}")
    _LOGGER.info(f"Info log message in {module_name}")
    _LOGGER.warning(f"Warning log message in {module_name}")
    _LOGGER.error(f"Error log message in {module_name}")
    _LOGGER.critical(f"Critical log message in {module_name}")

    # Exception message
    try:
        raise RuntimeError(f"Sample RuntimeError text in {module_name}")
    except RuntimeError:
        _LOGGER.exception(f"Exception log message in {module_name}")


if __name__ == "__main__":
    pytest.main([__file__])
