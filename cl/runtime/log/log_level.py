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


class LogLevel(IntEnum):
    """Indicates severity of the logged event."""

    DEBUG = 10
    """Detailed information, typically only of interest to a developer trying to diagnose a problem."""

    INFO = 20
    """Confirmation that things are working as expected."""

    WARNING = 30
    """Something unexpected happened, or an error might occur in the near future (e.g., disk space low)."""

    ERROR = 40
    """The program has not been able to perform some function but may still be able to continue running."""

    CRITICAL = 50
    """A critical error, indicating that the program may be unable to continue running."""
