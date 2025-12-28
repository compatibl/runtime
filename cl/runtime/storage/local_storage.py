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
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.typename import typename
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode
from cl.runtime.storage.local_binary_file import LocalBinaryFile
from cl.runtime.storage.local_text_file import LocalTextFile
from cl.runtime.storage.storage import Storage
from cl.runtime.storage.storage_key import StorageKey
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class LocalStorage(Storage):
    """Provides access to a filesystem or cloud blob storage service using a file-based API."""

    rel_dir: str = required()
    """Storage directory as path relative to project root."""

    _abs_dir: str = required(init=False)
    """Storage directory as absolute path."""

    def get_key(self) -> StorageKey:
        return StorageKey(storage_id=self.storage_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Combine with project root if a relative path, error otherwise
        if not os.path.isabs(self.rel_dir):
            self._abs_dir = os.path.join(ProjectLayout.get_project_root(), self.rel_dir)
        else:
            raise RuntimeError(f"{typename(type(self))}.rel_dir is not a relative path:\n{self.rel_dir}")

        # Create storage root directory if does not exist
        if not os.path.exists(self._abs_dir):
            os.makedirs(self._abs_dir)

    def open_text_file(self, rel_path: str, mode: str | TextFileMode) -> TextFile:
        self._check_lifecycle_phase()
        # Combine with root directory of the storage to get the absolute file path
        abs_path = self._get_file_abs_path(rel_path)
        mode_enum = self._to_text_file_mode_enum(mode)
        return LocalTextFile(abs_path=abs_path, mode=mode_enum).build()

    def open_binary_file(self, rel_path: str, mode: str | BinaryFileMode) -> BinaryFile:
        self._check_lifecycle_phase()
        # Combine with root directory of the storage to get the absolute file path
        abs_path = self._get_file_abs_path(rel_path)
        mode_enum = self._to_binary_file_mode_enum(mode)
        return LocalBinaryFile(abs_path=abs_path, mode=mode_enum).build()

    def _get_file_abs_path(self, rel_path: str) -> str:
        """Get the absolute path for the file."""
        if not os.path.isabs(rel_path):
            return os.path.join(self._abs_dir, rel_path)
        else:
            raise RuntimeError(f"Parameter rel_path is not a relative path:\nValue: {rel_path}")
