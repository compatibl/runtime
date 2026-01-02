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
from frozendict import frozendict
from typing_extensions import final
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import MAPPING_TYPES
from cl.runtime.records.typename import typenameof
from cl.runtime.settings.settings import Settings
from runtime.cl.runtime.file.project_layout import ProjectLayout


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

    def get_packages(self) -> tuple[str, ...]:
        """Return package_source_dirs keys as a tuple, ignoring their directories."""
        return tuple(self.package_source_dirs.keys())

    def get_source_and_stub_dirs(self) -> tuple[str, ...]:
        """Return source and stub directories relative to project root without duplicates."""
        return tuple(set(self.package_source_dirs.values()) | set(self.package_stub_dirs.values()))

    def configure_pythonpath(self) -> None:
        """
        Ensure all source and stub directories are in PYTHONPATH and sys.path.

        Directories are only added if they are not already present,
        irrespective of relative vs. absolute path format or OS separators.
        """

        # Prepare the list of source and stub directories
        project_root = ProjectLayout.get_project_root()
        package_paths = tuple(os.path.join(project_root, x) for x in self.get_source_and_stub_dirs())

        # Canonicalize existing paths in sys.path for comparison
        # This handles cross-OS separators and relative/absolute discrepancies
        existing_canonical_paths = {os.path.abspath(os.path.normpath(p)) for p in sys.path if p}

        # Identify which directories are actually missing
        paths_to_add = []
        for path in package_paths:
            canonical_path = os.path.abspath(os.path.normpath(path))
            if canonical_path not in existing_canonical_paths:
                paths_to_add.append(path)
                # Avoid adding the same dir twice if it's in both source and stub
                existing_canonical_paths.add(canonical_path)

        # If there are new directories, update the environment and current process
        if paths_to_add:
            # Update sys.path for the current running process
            sys.path.extend(paths_to_add)
            # Update os.environ["PYTHONPATH"] for any future subprocesses
            if current_pythonpath := os.environ.get("PYTHONPATH", ""):
                # Append to existing PYTHONPATH
                os.environ["PYTHONPATH"] = current_pythonpath + os.pathsep + os.pathsep.join(paths_to_add)
            else:
                # Initialize PYTHONPATH
                os.environ["PYTHONPATH"] = os.pathsep.join(paths_to_add)

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
