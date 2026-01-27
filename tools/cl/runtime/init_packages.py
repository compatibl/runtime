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

# Ensure bootstrap module can be found
locate.append_sys_path("../../..")

# Import bootstrap module first to configure PYTHONPATH and other settings
import cl.runtime.bootstrap  # isort: skip Prevent isort from moving this line

from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.settings.package_settings import PackageSettings
from cl.runtime.templates.jinja_template_engine import JinjaTemplateEngine


def init_packages() -> None:
    """Initialize package files for each package."""

    # Get template directory path relative to where the current Python file is located
    template_dir = str(Path(__file__).parent / "init_packages")

    # Create Jinja2 template engine
    engine = JinjaTemplateEngine().build()

    # Iterate over each package and render templates into the package root
    for package in PackageSettings.instance().get_packages():
        package_root = ProjectLayout.get_package_root(package)
        engine.render_dir(input_dir=template_dir, output_dir=package_root, data={"package": package})


if __name__ == '__main__':

    # Initialize package files
    init_packages()
