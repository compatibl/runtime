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


class FileType(IntEnum):
    """Binary content type enumeration."""

    JPG = auto()
    """Jpg image type."""

    JPEG = auto()
    """Jpeg image type."""

    HTML = auto()
    """Html content type."""

    PLOTLY = auto()
    """The output provided by Plotly Graphing Library."""

    PNG = auto()
    """PNG image type."""

    SVG = auto()
    """SVG image type."""

    FOR_CSV = auto()
    """Csv type."""

    ZIP = auto()
    """Zip type."""

    PDF = auto()
    """PDF type."""

    XLSX = auto()
    """Excel type."""
