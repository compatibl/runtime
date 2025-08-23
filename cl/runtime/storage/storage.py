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
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.contexts.lifecycle_mixin import LifecycleMixin
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode
from cl.runtime.storage.storage_key import StorageKey
from cl.runtime.storage.storage_mode import StorageMode
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class Storage(StorageKey, LifecycleMixin, RecordMixin, ABC):
    """Provides access to a filesystem or cloud blob storage service using a file-based API."""

    storage_mode: StorageMode = StorageMode.READ_WRITE
    """Determines what operations are permitted."""

    def get_key(self) -> StorageKey:
        return StorageKey(storage_id=self.storage_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.storage_id is None:
            # Use globally unique UUIDv7-based timestamp if not specified
            self.storage_id = Timestamp.create()

    @abstractmethod
    def open_text_file(self, rel_path: str, mode: str | TextFileMode) -> TextFile:
        """
        Open a text file in read, write or append mode.

        Note:
            The returned object is a context manager that must be used in a 'with' clause.

        Args:
            rel_path: Path to the file relative to the storage root.
            mode: Supported modes are 'r', 'w', 'a' strings or TextFileMode enum.
        """

    @abstractmethod
    def open_binary_file(self, rel_path: str, mode: str | BinaryFileMode) -> BinaryFile:
        """
        Open a binary file in read, write or append mode.

        Note:
            The returned object is a context manager that must be used in a 'with' clause.

        Args:
            rel_path: Path to the file relative to the storage root.
            mode: Supported modes are 'rb', 'wb', 'ab' strings or TextFileMode enum.
        """

    @classmethod
    def _normalize_rel_path(cls, rel_path: str) -> str:
        """Normalize relative path to standard format with Unix style separators."""
        if not os.path.isabs(rel_path):
            return os.path.normpath(rel_path).replace("\\", "/")
        else:
            raise RuntimeError(f"Not a relative path: {rel_path}")

    def _to_text_file_mode_enum(self, mode: str | TextFileMode) -> TextFileMode:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("r", TextFileMode.READ):
            return TextFileMode.READ
        elif mode in ("w", TextFileMode.WRITE):
            self._check_can_write()
            return TextFileMode.WRITE
        elif mode in ("a", TextFileMode.APPEND):
            self._check_can_write()
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

    def _to_binary_file_mode_enum(self, mode: str | BinaryFileMode) -> BinaryFileMode:
        """Convert mode string or enum to the representation that can be passed to the Python 'open' function."""
        if mode in ("rb", BinaryFileMode.READ):
            return BinaryFileMode.READ
        elif mode in ("wb", BinaryFileMode.WRITE):
            self._check_can_write()
            return BinaryFileMode.WRITE
        elif mode in ("ab", BinaryFileMode.APPEND):
            self._check_can_write()
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

    def _check_can_write(self) -> None:
        """Raise an error if the storage is not writable."""
        if self.storage_mode == StorageMode.READ_ONLY:
            storage_id_str = f" {self.storage_id}" if self.storage_id else ""
            raise RuntimeError(f"Cannot write to a read-only storage{storage_id_str}.")
        elif self.storage_mode != StorageMode.READ_WRITE:
            raise ErrorUtil.enum_value_error(self.storage_mode, StorageMode)
