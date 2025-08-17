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

from enum import IntEnum
from enum import auto


class FileKind(IntEnum):
    """Format of the file contents, some values match to more than one file extension."""

    JPG = auto()
    """JPEG image."""

    HTML = auto()
    """HTML content."""

    PLOTLY = auto()
    """The output provided by Plotly Graphing Library."""

    PNG = auto()
    """PNG image."""

    SVG = auto()
    """SVG image."""

    CSV = auto()
    """CSV data."""

    ZIP = auto()
    """ZIP archive."""

    PDF = auto()
    """PDF document."""

    XLSX = auto()
    """Excel file."""
