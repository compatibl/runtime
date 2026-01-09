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

import os
from typing import Literal


class OsUtil:  # TODO: Review how this class is used
    """Helper methods for the operating system."""

    @classmethod
    def is_windows(cls) -> bool:
        """Return true if the operating system is Windows."""
        return os.name == "nt"

    @classmethod
    def newline_sequence(cls) -> Literal["\n", "\r\n"]:
        """Return \r\n on Windows and \n otherwise."""
        return "\r\n" if cls.is_windows() else "\n"
