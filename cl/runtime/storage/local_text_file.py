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

from dataclasses import dataclass
from typing import Any
from typing_extensions import Self

from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class LocalTextFile(TextFile):
    """Provides access to a local text file."""

    abs_path: str
    """The absolute path to the file."""

    mode: TextFileMode
    """Enumeration for Python text file modes 'r', 'w', and 'a'."""

    _file: Any = required()
    """The object returned by the Python 'open' function."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Open the file using the specified mode
        mode_str = self.get_mode_str()
        self._file = open(self.abs_path, mode_str)

    def read(self) -> str:
        self._check_lifecycle_phase()
        return self._file.read()

    def write(self, text: str) -> None:
        self._check_lifecycle_phase()
        self._file.write(text)

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        super().__enter__()
        self._file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        super().__exit__(exc_type, exc_val, exc_tb)
        self._file.__exit__(exc_type, exc_val, exc_tb)

    def get_mode_str(self) -> str:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if self.mode == TextFileMode.READ:
            return "r"
        elif self.mode == TextFileMode.WRITE:
            return "w"
        elif self.mode == TextFileMode.APPEND:
            return "a"
        else:
            raise ErrorUtil.enum_value_error(self.mode, TextFileMode)
