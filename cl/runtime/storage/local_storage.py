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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode
from cl.runtime.storage.local_binary_file import LocalBinaryFile
from cl.runtime.storage.local_text_file import LocalTextFile
from cl.runtime.storage.storage import Storage
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.storage_key import StorageKey
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class LocalStorage(Storage):
    """Provides access to a filesystem or cloud blob storage service using a common API."""

    root_dir: str = required()
    """Root directory in local storage relative to which file paths are specified."""

    def get_key(self) -> StorageKey:
        return StorageKey(storage_id=self.storage_id).build()

    def open_text_file(self, file_path: str, mode: str  | TextFileMode) -> TextFile:
        """
        Open a text file for reading and/or writing, valid modes are 'r', 'w', and 'a' or the corresponding enums.
        The returned object is a context manager that automatically closes the file on exit from 'with' block.
        """
        full_path = os.path.join(self.root_dir, file_path)
        text_mode_str = self._to_text_mode_str(mode)
        return LocalTextFile(_file=open(full_path, text_mode_str))

    def open_binary_file(self, file_path: str, mode: str  | BinaryFileMode) -> BinaryFile:
        """
        Open a binary file for reading and/or writing, valid modes are 'r', 'w', and 'a' or the corresponding enums.
        The returned object is a context manager that automatically closes the file on exit from 'with' block.
        """
        full_path = os.path.join(self.root_dir, file_path)
        binary_mode_str = self._to_binary_mode_str(mode)
        return LocalBinaryFile(_file=open(full_path, binary_mode_str))

    @classmethod
    def _to_text_mode_str(cls, mode: str  | TextFileMode) -> str:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("r", TextFileMode.READ):
            return "r"
        elif mode in ("w", TextFileMode.WRITE):
            return "w"
        elif mode in ("a", TextFileMode.APPEND):
            return "a"
        else:
            if isinstance(mode, TextFileMode):
                mode_str = mode
            elif isinstance(mode, TextFileMode):
                mode_str = mode.name
            else:
                raise RuntimeError(f"Invalid type for mode: {type(mode)}, expected str or TextFileMode.")
            raise RuntimeError(
                f"Mode {mode_str} is not supported when opening a text file.\n"
                f"Valid modes are: 'r', 'w', 'a' or TextFileMode enum.")

    @classmethod
    def _to_binary_mode_str(cls, mode: str  | BinaryFileMode) -> str:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("rb", BinaryFileMode.READ):
            return "rb"
        elif mode in ("wb", BinaryFileMode.WRITE):
            return "wb"
        elif mode in ("ab", BinaryFileMode.APPEND):
            return "ab"
        else:
            if isinstance(mode, str):
                mode_str = mode
            elif isinstance(mode, BinaryFileMode):
                mode_str = mode.name
            else:
                raise RuntimeError(f"Invalid type for mode: {type(mode)}, expected str or BinaryFileMode.")
            raise RuntimeError(
                f"Mode {mode_str} is not supported when opening a binary file.\n"
                f"Valid modes are: 'rb', 'wb', 'ab' or BinaryFileMode enum.")
