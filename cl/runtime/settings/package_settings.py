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
from frozendict import frozendict
from typing_extensions import final
from cl.runtime.project.project_checks import ProjectChecks
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_TYPES
from cl.runtime.records.typename import typenameof
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class PackageSettings(Settings):
    """Settings for the package location, dependencies, and requirements."""

    package_source_dirs: Mapping[str, str] = required()
    """
    Mapping of package (e.g., cl.runtime) to its source directory relative to project root.
    If the package is directly under project root, specify "." as the value.
    """

    package_stub_dirs: Mapping[str, str] = required()
    """
    Mapping of package (e.g., cl.runtime) to its stubs directory relative to project root.
    If this field is None, stub_dirs will be initialized to source_dirs.
    """

    package_test_dirs: Mapping[str, str] = required()
    """
    Mapping of package (e.g., cl.runtime) to its tests directory relative to project root.
    If this field is None, test_dirs will be initialized to 'tests' subdirectories of source_dirs.
    """

    package_requirements: Sequence[str] | None = None
    """This list is used to generate the requirements in requirements.txt and pyproject.toml."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Perform validation
        self.package_source_dirs = self._normalize_dirs(self.package_source_dirs, field_name="package_source_dirs")
        self.package_stub_dirs = self._normalize_dirs(self.package_stub_dirs, field_name="package_stub_dirs")
        self.package_test_dirs = self._normalize_dirs(self.package_test_dirs, field_name="package_test_dirs")

        if self.package_stub_dirs is None:
            # If stub_dirs is None, it will be initialized to source_dirs
            self.package_stub_dirs = self.package_source_dirs

        if self.package_test_dirs is None:
            # If test_dirs is None, it will be initialized to 'tests' subdirectories of source_dirs
            self.package_test_dirs = frozendict(
                {k: os.path.join(v, "tests") for k, v in self.package_source_dirs.items()}
            )
        else:
            # Otherwise ensure it does not add any new packages relative to source dirs
            if missing_source_packages := self.package_test_dirs.keys() - self.package_source_dirs.keys():
                raise RuntimeError(
                    f"PackageSettings.package_test_dirs specifies tests for packages that are not "
                    f"defined in PackageSettings.package_source_dirs: {', '.join(sorted(missing_source_packages))}"
                )

        # Validate package requirements format
        if self.package_requirements is not None:
            ProjectChecks.guard_requirements(self.package_requirements)

    def get_packages(self) -> tuple[str, ...]:
        """Return package_source_dirs keys as a tuple, ignoring their directories."""
        # Convert to lists with preserved order
        source_packages = list(self.package_source_dirs.keys())
        stub_packages = list(self.package_stub_dirs.keys())

        # Deduplicate preserving order in each list, source first, and return as tuple
        return tuple(dict.fromkeys(source_packages + stub_packages))

    def get_package_dirs(self) -> tuple[str, ...]:
        """
        Return source and stub directories relative to project root without duplicates. Result order is
        all source directories first (in their listed order), then stub directories (in their listed order).
        """
        # Convert to lists with preserved order
        source_dirs = list(self.package_source_dirs.values())
        stub_dirs = list(self.package_stub_dirs.values())

        # Deduplicate preserving order in each list, source first, and return as tuple
        return tuple(dict.fromkeys(source_dirs + stub_dirs))

    def configure_paths(self) -> None:
        """
        Ensure all source and stub directories are in sys.path and PYTHONPATH

        Directories are only added if they are not already present,
        irrespective of relative vs. absolute path format or OS separators.
        """

        # Absolute paths to source and stub directories for all packages
        project_root = ProjectLayout.get_project_root()
        package_paths = tuple(os.path.join(project_root, x) for x in self.get_package_dirs())
        package_paths = self._normalize_paths(package_paths)

        # Add to sys.path without duplicates
        sys_path_set = set(self._normalize_paths(sys.path))
        for path in package_paths:
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

    @classmethod
    def _normalize_dirs(cls, dirs: Mapping[str, str] | None, *, field_name: str) -> frozendict[str, str] | None:
        """
        Validate the mapping provided for source, stub or test dirs, accept None as valid.

        Notes:
            - The argument must be a mapping
            - Keys must be valid dot-delimited package names
            - Directories must be specified as relative paths to project root, absolute paths are not accepted
        """
        if dirs is None:
            return None

        # Validate that it is a mapping
        if not isinstance(dirs, MAPPING_TYPES):
            raise RuntimeError(f"PackageSettings.{field_name} must be a mapping, but got {typenameof(dirs)}.")

        for package_name, path in dirs.items():
            # Validate keys: valid dot-delimited package names
            # We check if each part of the dot-split string is a valid Python identifier
            if not all(part.isidentifier() for part in package_name.split(".")):
                raise ValueError(
                    f"Invalid package name '{package_name}' in {field_name}. "
                    "Keys must be valid dot-delimited package names."
                )

            # Validate values: must be relative paths
            if os.path.isabs(path):
                raise ValueError(
                    f"Invalid path '{path}' in {field_name}. "
                    "Directories must be specified as relative paths to project root."
                )

        return frozendict(dirs)
