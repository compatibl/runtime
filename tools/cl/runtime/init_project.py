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
from pathlib import Path

import locate
from jinja2 import Environment, FileSystemLoader

# Ensure bootstrap module can be found
locate.append_sys_path("../../..")

# Import bootstrap module first to configure PYTHONPATH and other settings
import cl.runtime.bootstrap  # isort: skip Prevent isort from moving this line

from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.prebuild.init_file_util import InitFileUtil
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.settings.package_settings import PackageSettings


def init_project() -> None:
    """Initialize project files."""

    # Get package settings
    package_settings = PackageSettings.instance()

    # Extract unique package directory names (excluding stubs and ".")
    # Filter to only get main packages (cl.*) and their directory values
    package_dirs = PackageSettings.instance().get_package_dirs()

    # Get project root
    project_root = ProjectLayout.get_project_root()

    # Get template directory (where this script is located)
    script_dir = Path(__file__).parent
    template_dir = script_dir / "project"

    # Create Jinja2 environment with settings to preserve exact formatting
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    # Template mappings: (template_path, output_path)
    templates = [
        ("cursor/config.json.j2", ".cursor/config.json"),
        ("pyproject.toml.j2", "pyproject.toml"),
        ("vscode/launch.json.j2", ".vscode/launch.json"),
        ("vscode/settings.json.j2", ".vscode/settings.json"),
    ]

    # Render each template
    for template_path, output_path in templates:
        template = env.get_template(template_path)
        content = template.render(packages=package_dirs)

        # Create output file path
        output_file = os.path.join(project_root, output_path)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Write rendered content with newline='' to preserve exact line endings from template
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            f.write(content)


if __name__ == '__main__':

    # Initialize project files
    init_project()
