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
    The environment kind determines the policies for data protection and retention
    and is used to select the Dynaconf environment.
    """

    PROD = auto()
    """
    Persistent production environment, destructive actions require explicit authorization.
    Activates Dynaconf setting 'production'.
    """

    STAGING = auto()
    """
    Persistent staging environment, destructive actions require explicit authorization.
    Activates Dynaconf setting 'staging'.
    """

    DEV = auto()
    """
    Persistent development environment, destructive actions do not require explicit authorization.
    Activates Dynaconf setting 'development'.
    """

    TEMP = auto()
    """
    Temporary environment for testing or development, initialized and deleted automatically on each run.
    Activates Dynaconf setting 'development' when outside pytest, or 'testing' when inside pytest.
    """

