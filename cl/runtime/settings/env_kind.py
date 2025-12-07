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


class EnvKind(IntEnum):
    """
    The environment kind determines the policies for data protection and retention.

    Notes:
        It is checked for compatibility with the Dynaconf environment selected using CL_RUNTIME_ENV.
    """

    PROD = auto()
    """Requires dynaconf_env=production, database cannot be deleted from code."""

    UAT = auto()
    """Requires dynaconf_env=staging, database can be deleted from code with explicit user approval."""

    DEV = auto()
    """Requires dynaconf_env=development, database deletion is requested on each server start (denied by default)."""

    TEMP = auto()
    """Requires dynaconf_env=development, database is DELETED AUTOMATICALLY on each server start."""

    TEST = auto()
    """Requires dynaconf_env=testing, database is DELETED AUTOMATICALLY before and after each test."""
