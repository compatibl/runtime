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
import platform
from pathlib import Path

import locate
from jinja2 import Environment, FileSystemLoader

from cl.runtime.contexts.os_util import OsUtil

# Ensure bootstrap module can be found
locate.append_sys_path("../../..")

# Import bootstrap module first to configure PYTHONPATH and other settings
import cl.runtime.bootstrap  # isort: skip Prevent isort from moving this line

from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings


def transform_part(part: str) -> str:
    """Replace dot_ prefix by . in file or directory name token."""
    return "." + part.removeprefix("dot_") if part.startswith("dot_") else part


def init_project() -> None:
    """Initialize project files."""

    # Get package settings
    package_settings = PackageSettings.instance()

    # Extract unique package directory names (excluding stubs and ".")
    # Filter to only get main packages (cl.*) and their directory values
    package_dirs = PackageSettings.instance().get_package_dirs()

    # Get project root
    project_root = Path(ProjectLayout.get_project_root())

    # Get template directory (where this script is located)
    script_dir = Path(__file__).parent
    template_dir = script_dir / "project"

    # Create Jinja2 environment with settings to preserve exact formatting
    # Use trim_blocks to remove newlines after block tags, but preserve content newlines
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        newline_sequence=OsUtil.newline_sequence(),
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )

    # Find all .j2 files recursively in the template directory
    template_files = list(template_dir.rglob("*.j2"))

    # Process each template file
    for template_file in template_files:
        # Get relative path from template directory
        relative_path = template_file.relative_to(template_dir)

        # Convert to string and split into parts
        path_parts = list(relative_path.parts)

        output_path = Path(*[
            # Remove suffix .j2 only from the last part of the path (the filename)
            transform_part(p.removesuffix(".j2") if i == len(path_parts) - 1 else p)
            for i, p in enumerate(path_parts)
        ])

        # Jinja2 expects POSIX-style paths even on Windows
        template_path_str = relative_path.as_posix()

        # Get template and render
        template = env.get_template(template_path_str)
        content = template.render(packages=package_dirs)

        # Create output file path
        output_file = project_root / output_path

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


if __name__ == '__main__':

    # Initialize project files
    init_project()
