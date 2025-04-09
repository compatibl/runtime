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

from enum import IntEnum
from enum import auto


class AppEnv(IntEnum):
    """The deployment environment setting determines the policies for data retention and deletion."""

    PROD = auto()
    """Production environment, persistent across runs, destructive actions via the API are prohibited."""

    UAT = auto()
    """User acceptance testing environment, persistent across runs, destructive actions via the API are prohibited."""

    DEV = auto()
    """Development environment, initialized on each run, destructive actions via the API are permitted."""

    TEMP = auto()
    """Temporary environment, initialized on each run, deleted automatically at the end of the run."""
