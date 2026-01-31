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
import sys
from dataclasses import dataclass
from typing import Mapping
from typing import Sequence

import frozendict
from typing_extensions import final  # TODO: !!! Do not import from typing_extensions

from cl.runtime.project.project_checks import ProjectChecks
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class PackageSettings(Settings):
    """Package-specific settings, usual Dynaconf overrides from env vars or .env do not apply."""

    package_dirs: Mapping[str, str] = required()
    """
    Ordered mapping of package source namespace to package directory relative to project root
    where dependent packages follow the packages they depend on.
    """

    package_namespace: str = required()
    """Namespace of the package, e.g. 'cl.runtime'."""

    package_stubs_namespace: str = "stubs.{package_namespace}"
    """Stubs namespace of the package, e.g. 'stubs.cl.runtime' (defaults to stubs.{package_namespace})."""

    package_source_dir: str = "."
    """Source dir relative to project root (defaults to '.', i.e. placement directly under project root)."""

    package_stubs_dir: Mapping[str, str] = "stubs"
    """Stubs dir relative to project root (defaults to 'stubs')."""

    package_tests_dir: Mapping[str, str] = "tests"
    """Tests dir relative to project root (defaults to 'tests')."""

    package_dependencies: Sequence[str] | None = None
    """Used to generate dependencies in pyproject.toml."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Perform variable substitution in package_stubs_namespace
        self.package_stubs_namespace = self.package_stubs_namespace.format(package_namespace=self.package_namespace)

        # Initialize and validate package dependencies
        if self.package_dependencies is None:
            self.package_dependencies = []
        ProjectChecks.guard_requirements(self.package_dependencies)

    def get_packages(self) -> tuple[str, ...]:
        """Ordered tuple of package namespaces (keys) from package_dirs mapping."""
        return tuple(self.package_dirs.keys())

    def get_dirs(self) -> tuple[str, ...]:
        """Ordered tuple of package directories (values) from package_dirs mapping with duplicates removed."""
        return tuple(dict.fromkeys(self.package_dirs.values()))

    def configure_paths(self) -> None:
        """
        Ensure all source and stub directories are in sys.path and PYTHONPATH

        Directories are only added if they are not already present,
        irrespective of relative vs. absolute path format or OS separators.
        """

        # Absolute paths to source and stub directories for all packages
        project_root = ProjectLayout.get_project_root()
        package_paths = tuple(os.path.join(project_root, x) for x in self.package_dirs.values())
        package_paths = self._normalize_paths(package_paths)

        # Add to sys.path without duplicates
        sys_path_set = set(self._normalize_paths(sys.path))
        for path in self._normalize_paths(list(self.package_dirs.values())):
            if path not in sys_path_set:
                # Add path from package_paths
                sys.path.append(path)

        # Add to PYTHONPATH without duplicates
        python_path_str = os.environ.get("PYTHONPATH", "")
        python_path_set = set(self._normalize_paths(python_path_str.split(os.pathsep)))
        python_path_added = False
        for path in package_paths:
            if path not in python_path_set:
                python_path_added = True
                if python_path_str:
                    # Add separator unless empty
                    python_path_str += os.pathsep
                # Add path from package_paths
                python_path_str += path
        if python_path_added:
            # Only if paths have been added
            os.environ["PYTHONPATH"] = python_path_str

    @classmethod
    def _normalize_paths(cls, paths: Sequence[str]) -> tuple[str, ...]:
        """Convert paths to canonical format."""
        return tuple(os.path.abspath(os.path.normpath(p)) for p in paths)
