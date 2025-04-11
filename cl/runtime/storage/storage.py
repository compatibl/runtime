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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode
from cl.runtime.storage.storage_key import StorageKey
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class Storage(StorageKey, RecordMixin[StorageKey], ABC):
    """Provides access to a filesystem or cloud blob storage service using a common API."""

    def get_key(self) -> StorageKey:
        return StorageKey(storage_id=self.storage_id).build()

    @abstractmethod
    def open_text_file(self, file_path: str, mode: str | TextFileMode) -> TextFile:
        """
        Open a text file for reading and/or writing, valid modes are 'r', 'w', and 'a' or the corresponding enums.
        The returned object is a context manager that automatically closes the file on exit from 'with' block.
        """

    @abstractmethod
    def open_binary_file(self, file_path: str, mode: str | BinaryFileMode) -> BinaryFile:
        """
        Open a binary file for reading and/or writing, valid modes are 'r', 'w', and 'a' or the corresponding enums.
        The returned object is a context manager that automatically closes the file on exit from 'with' block.
        """

    @classmethod
    def _to_text_mode_enum(cls, mode: str | TextFileMode) -> TextFileMode:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("r", TextFileMode.READ):
            return TextFileMode.READ
        elif mode in ("w", TextFileMode.WRITE):
            return TextFileMode.WRITE
        elif mode in ("a", TextFileMode.APPEND):
            return TextFileMode.APPEND
        else:
            if isinstance(mode, str):
                mode_str = mode
            elif isinstance(mode, TextFileMode):
                mode_str = mode.name
            else:
                raise RuntimeError(f"Invalid type for mode: {type(mode)}, expected str or TextFileMode enum.")
            raise RuntimeError(
                f"Mode {mode_str} is not supported when opening a text file.\n"
                f"Valid modes are: 'r', 'w', 'a' or TextFileMode enum."
            )

    @classmethod
    def _to_binary_mode_enum(cls, mode: str | BinaryFileMode) -> BinaryFileMode:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("rb", BinaryFileMode.READ):
            return BinaryFileMode.READ
        elif mode in ("wb", BinaryFileMode.WRITE):
            return BinaryFileMode.WRITE
        elif mode in ("ab", BinaryFileMode.APPEND):
            return BinaryFileMode.APPEND
        else:
            if isinstance(mode, str):
                mode_str = mode
            elif isinstance(mode, BinaryFileMode):
                mode_str = mode.name
            else:
                raise RuntimeError(f"Invalid type for mode: {type(mode)}, expected str or BinaryFileMode enum.")
            raise RuntimeError(
                f"Mode {mode_str} is not supported when opening a binary file.\n"
                f"Valid modes are: 'rb', 'wb', 'ab' or BinaryFileMode enum."
            )
