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
from cl.runtime.storage.text_file import TextFile


@dataclass(slots=True, kw_only=True)
class LocalTextFile(TextFile):
    """Provides access to a local text file."""

    _file: Any
    """The object returned by the open() function."""

    def read(self) -> str:
        """Read text."""
        return self._file.read()

    def write(self, text: str) -> int:
        return self._file.write(text)

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource disposal."""
        self._file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Supports 'with' operator for resource disposal."""
        self._file.__exit__(exc_type, exc_val, exc_tb)
        # Allow exceptions to propagate
        return False
