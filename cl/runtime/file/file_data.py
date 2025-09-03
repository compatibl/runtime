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
from cl.runtime.file.file_kind import FileKind
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class FileData(DataclassMixin):
    """Display the specified embedded binary content."""

    name: str | None = None  # TODO: Consider revising to filename
    """Content name."""

    file_kind: FileKind | None = None
    """Format of the file contents, some values match to more than one file extension."""

    file_bytes: bytes = required()
    """Embedded binary content to be displayed as the current view."""
