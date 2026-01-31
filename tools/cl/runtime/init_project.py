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

from pathlib import Path

import locate # isort: skip Prevent isort from moving this line

from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.project.project_layout_kind import ProjectLayoutKind

# Ensure bootstrap module can be found
locate.append_sys_path("../../..")

# Import bootstrap module first to configure PYTHONPATH and other settings
import cl.runtime.bootstrap  # isort: skip Prevent isort from moving this line

from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def init_project() -> None:
    """Initialize project files."""

    if (project_layout := ProjectLayout.get_project_layout_kind()) != ProjectLayoutKind.MULTIREPO:
        raise RuntimeError(f"Cannot run init_multirepo script when project layout is {project_layout.name.lower()}.")

    # Extract unique package directory names (excluding stubs and ".")
    # Filter to only get main packages (cl.*) and their directory values
    package_dirs = PackageSettings.instance().get_dirs()

    # Get project root
    project_root = Path(ProjectLayout.get_project_root())

    # Get template directory path relative to where the current Python file is located
    if (layout_kind := ProjectLayout.get_project_layout_kind()) == ProjectLayoutKind.MULTIREPO:
        template_dir = str(Path(__file__).parent / "init_project/multirepo")
    elif layout_kind == ProjectLayoutKind.MONOREPO:
        template_dir = str(Path(__file__).parent / "init_project/monorepo")
    else:
        raise ErrorUtil.enum_value_error(layout_kind, ProjectLayoutKind)

    # Create Jinja2 template engine and render all templates
    engine = JinjaTemplateEngine().build()
    engine.render_dir(input_dir=template_dir, output_dir=project_root, data={"packages": package_dirs})


if __name__ == '__main__':

    # Initialize project files
    init_project()
