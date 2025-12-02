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
from typing import Sequence
from cl.runtime.file.reader_key import ReaderKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Reader(ReaderKey, RecordMixin, ABC):
    """Read records from the specified storage and save them to the active data source."""

    def get_key(self) -> ReaderKey:
        return ReaderKey(reader_id=self.reader_id).build().build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.reader_id is None:
            self.reader_id = Timestamp.create()

    @abstractmethod
    def load_all(
        self,
        *,
        dirs: Sequence[str],
        ext: str,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> tuple[RecordMixin]:
        """
        Load records from files in the specified dirs with the specified extension.

        Args:
            dirs: Directories where file search is performed
            ext: File extension to search for without the leading dot (e.g., "json" or "csv")
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """
