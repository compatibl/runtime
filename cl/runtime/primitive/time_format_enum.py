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


class TimeFormatEnum(IntEnum):
    """Format used to serialize and deserialize dt.datetime."""

    PASSTHROUGH = auto()
    """Do not apply any transformation during serialization or deserialization."""

    DEFAULT = auto()
    """ISO 8601 time string to millisecond precision without timezone: hh:mm:ss.fff"""

    ISO_INT = auto()
    """ISO 8601 readable int to millisecond precision without timezone: hhmmssfff"""
