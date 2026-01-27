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

import platform
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.data_mixin import TData, DataMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.templates.template_engine_key import TemplateEngineKey

def transform_part(part: str) -> str:
    """Replace dot_ prefix by . in file or directory name token."""
    return "." + part.removeprefix("dot_") if part.startswith("dot_") else part

@dataclass(slots=True, kw_only=True)
class TemplateEngine(TemplateEngineKey, RecordMixin, ABC):
    """Engine to perform template rendering."""

    def get_key(self) -> TemplateEngineKey:
        return TemplateEngineKey(engine_id=self.engine_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.engine_id is None:
            # Use globally unique UUIDv7-based timestamp if not specified
            self.engine_id = Timestamp.create()

    @abstractmethod
    def render(self, text: str, data: DataMixin | dict[str, Any]) -> str:
        """Render the template text by taking parameters from the data object."""

    def render_dir(self, *, input_dir: str, output_dir, data: DataMixin | dict[str, Any]) -> None:
        """
        Render all templates with filename.ext.j2 name in input_dir and its subdirectories by taking parameters
        from data object or dict, write output to filename.ext in the matching subdirectory of output_dir.
        """

        # Find all .j2 files recursively in input_dir
        template_files = list(Path(input_dir).rglob("*.j2"))

        # Process each template file
        for template_file in template_files:

            # Get relative path from input_dir
            relative_path = template_file.relative_to(input_dir)

            # Convert to string and split into parts
            path_parts = list(relative_path.parts)

            # Output path relative to output_dir
            output_relative_path = Path(*[
                # Remove suffix .j2 only from the last part of the path (the filename)
                transform_part(p.removesuffix(".j2") if i == len(path_parts) - 1 else p)
                for i, p in enumerate(path_parts)
            ])

            # Read template file content and render
            template_text = template_file.read_text(encoding="utf-8")
            content = self.render(template_text, data)

            # Create output file path
            output_file = output_dir / output_relative_path

            # Create output directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Normalize content to use LF, then let Python convert based on newline parameter
            # Replace any existing CRLF or CR with LF
            content = content.replace("\r\n", "\n").replace("\r", "\n")

            # Use CRLF on Windows, LF on Linux
            newline_char = "\r\n" if platform.system() == "Windows" else "\n"

            # Write rendered content with OS-appropriate line endings
            with open(output_file, "w", encoding="utf-8", newline=newline_char) as f:
                f.write(content)
