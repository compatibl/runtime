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
from dataclasses import dataclass
from typing import Any
from typing_extensions import Self
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode


@dataclass(slots=True, kw_only=True)
class LocalBinaryFile(BinaryFile):
    """Provides access to a local text file."""

    abs_path: str
    """The absolute path to the file."""

    mode: BinaryFileMode
    """Enumeration for Python binary file modes 'rb', 'wb', and 'ab'."""

    _file: Any = required()
    """The object returned by the Python 'open' function."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Check if the directory exists
        if not os.path.exists(abs_dir := os.path.dirname(self.abs_path)):
            if self.mode in (BinaryFileMode.WRITE, BinaryFileMode.APPEND):
                # Create on demand in WRITE or APPEND mode
                os.makedirs(abs_dir)
            elif self.mode == BinaryFileMode.READ:
                # Do not create on demand in READ mode
                file_name = os.path.basename(self.abs_path)
                raise RuntimeError(
                    f"Directory does not exist for read operation:\nDirectory: {abs_dir}Filename: {file_name}\n"
                )
            else:
                raise ErrorUtil.enum_value_error(self.mode, BinaryFileMode)

        # Open the file using the specified mode
        mode_str = self.get_mode_str()
        self._file = open(self.abs_path, mode_str)

    def read(self) -> bytes:
        return self._file.read()

    def write(self, data: bytes) -> None:
        return self._file.write(data)

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__enter__()
        self._file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__exit__(exc_type, exc_val, exc_tb)
        self._file.__exit__(exc_type, exc_val, exc_tb)

    def get_mode_str(self) -> str:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if self.mode == BinaryFileMode.READ:
            return "rb"
        elif self.mode == BinaryFileMode.WRITE:
            return "wb"
        elif self.mode == BinaryFileMode.APPEND:
            return "ab"
        else:
            raise ErrorUtil.enum_value_error(self.mode, BinaryFileMode)
