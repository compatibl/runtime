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
from typing import Iterable

from cl.runtime.project.project_layout_kind import ProjectLayoutKind
from cl.runtime.records.typename import typename

# Possible project root locations for each layout relative to this module
MULTIREPO_ROOT_DIR = os.path.normpath(Path(__file__).parents[4])
MONOREPO_ROOT_DIR = os.path.normpath(Path(__file__).parents[3])

# Filenames used to detect project root
root_filenames = [".env", "settings.yaml", "settings.json", "settings.toml"]

PROJECT_ROOT = None
PROJECT_LAYOUT_KIND: ProjectLayoutKind | None = None
try:
    if os.path.exists(MULTIREPO_ROOT_DIR):
        # Multirepo root takes priority but only if it contains one of the settings files
        if any(os.path.exists(os.path.join(MULTIREPO_ROOT_DIR, x)) for x in root_filenames):
            PROJECT_ROOT = MULTIREPO_ROOT_DIR
            PROJECT_LAYOUT_KIND = ProjectLayoutKind.MULTIREPO
# Handle the possibility that directory access is prohibited
except FileNotFoundError:
    pass
except PermissionError:
    pass

if PROJECT_ROOT is None:
    try:
        if os.path.exists(MONOREPO_ROOT_DIR):
            # Monorepo directory is searched next
            if any(os.path.exists(os.path.join(MONOREPO_ROOT_DIR, x)) for x in root_filenames):
                PROJECT_ROOT = MONOREPO_ROOT_DIR
                PROJECT_LAYOUT_KIND = ProjectLayoutKind.MONOREPO
    # Handle the possibility that directory access is prohibited
    except FileNotFoundError:
        pass
    except PermissionError:
        pass

# Error if still not found
if PROJECT_ROOT is None:
    root_filenames_str = "\n".join(root_filenames)
    raise RuntimeError(
        f"Project root could not be confirmed by the presence of at least one of the following files:\n"
        f"{root_filenames_str}\n\n"
        f"Potential project root locations searched:\n"
        f"Multirepo root: {MULTIREPO_ROOT_DIR}\n"
        f"Monorepo root: {MONOREPO_ROOT_DIR}\n"
    )


class ProjectLayout:  # TODO: !!!! Derive from Settings or rename to ProjectUtil or ProjectLayout and make static
    """
    Information about the project location and layout used to search for settings and packages.
    This class finds the location of .env or settings.yaml and detects one of two supported layouts:

    Multirepo layout (suitable for submodules or subtree git setup for each package):
        - project root (first level of multirepo layout)
            -- project files
            -- package root (second level of multirepo layout)
                --- package files (files from each package are under a separate package root)

    Monorepo layout (suitable for interleaved git merge of packages under a common root):
        - project and packages root (single-level monorepo layout)
            -- project files
            -- package files (files from all packages are interleaved under a common root)
    """

    @classmethod
    def get_project_layout_kind(cls) -> ProjectLayoutKind:
        """Specifies monorepo vs multirepo project layout."""
        return PROJECT_LAYOUT_KIND

    @classmethod
    def get_project_root(cls) -> str:
        """Project root directory is the location of .env or settings.yaml file."""
        return PROJECT_ROOT

    @classmethod
    def get_resources_root(cls) -> str:
        """Contains resources that persist across multiple code runs."""
        return os.path.join(PROJECT_ROOT, "resources")

    @classmethod
    def get_package_root(cls, package: str) -> str:
        """
        Package root directory for the specified package, same as project root in monorepo layout
        and project_root/package_name for multirepo layout. Not the same as get_source_root.

        Args:
            package: Dot-delimited package root, e.g. 'cl.runtime'
        """
        package_tokens = package.split(".")
        package_tokens_len = len(package_tokens)
        source_root = cls.get_source_root(package)
        result = os.path.normpath(str(Path(source_root).parents[package_tokens_len - 1]))
        return result

    @classmethod
    def get_source_root(cls, package: str) -> str:
        """
        Source code root directory (the entry in PYTHONPATH) for the specified package.

        Notes:
            Error if the directory does not contain __init__.py

        Args:
            package: Dot-delimited package root, e.g. 'cl.runtime'
        """
        relative_path = package.replace(".", os.sep)
        if PROJECT_LAYOUT_KIND == ProjectLayoutKind.MONOREPO:
            # Monorepo layout, search directly under project root
            search_paths = [os.path.normpath(os.path.join(PROJECT_ROOT, relative_path, "__init__.py"))]
        elif PROJECT_LAYOUT_KIND == ProjectLayoutKind.MULTIREPO:
            # Multirepo layout, check each dot-delimited package token in reverse order as potential package root
            package_tokens = package.split(".")
            package_tokens.reverse()
            search_paths = [
                os.path.normpath(os.path.join(PROJECT_ROOT, x, relative_path, "__init__.py")) for x in package_tokens
            ]
        else:
            raise RuntimeError(f"PROJECT_LAYOUT_KIND must be MONOREPO or MULTIREPO.")

        # Find the first directory with __init__.py
        init_path = next((x for x in search_paths if os.path.exists(x)), None)
        if init_path is not None:
            result = os.path.normpath(os.path.dirname(init_path))
            return result
        else:
            search_paths_str = "\n".join(search_paths)
            raise RuntimeError(
                f"Did not find  __init__.py for package '{package}'. Location searched:\n{search_paths_str}\n"
            )

    @classmethod
    def get_stubs_root(cls, package: str) -> str | None:
        """
        Stubs root directory for the specified package.

        Notes:
            Error if the directory does not contain __init__.py

        Args:
            package: Dot-delimited package root, e.g. 'cl.runtime'
        """
        package_tokens = package.split(".")
        package_tokens_len = len(package_tokens)
        source_root = cls.get_source_root(package)
        common_root = str(Path(source_root).parents[package_tokens_len - 1])
        if package_tokens[0] == "tests":
            # Do not look for stubs relative to tests
            return None
        elif package_tokens[0] == "stubs":
            # Stubs package is specified directly
            return source_root
        else:
            # Look for stubs package relative to source, return if exists
            stubs_root = os.path.normpath(os.path.join(common_root, "stubs", *package_tokens))
            if os.path.exists(stubs_root):
                return stubs_root
            else:
                return None

    @classmethod
    def get_tests_root(cls, package: str) -> str | None:
        """
        Tests root directory for the specified package.

        Notes:
            The presence of __init__.py is not required for tests

        Args:
            package: Dot-delimited package root, e.g. 'cl.runtime'
        """
        package_tokens = package.split(".")
        package_tokens_len = len(package_tokens)
        source_root = cls.get_source_root(package)
        common_root = str(Path(source_root).parents[package_tokens_len - 1])
        if package_tokens[0] == "tests":
            # Tests package is specified directly
            return source_root
        elif package_tokens[0] == "stubs":
            # Do not look for tests package relative to stubs
            return None
        else:
            # Look for tests package relative to source, return if exists
            tests_root = os.path.normpath(os.path.join(common_root, "tests", *package_tokens))
            if os.path.exists(tests_root):
                return tests_root
            else:
                return None

    @classmethod
    def get_preloads_root(cls, package: str) -> str | None:
        """Preloads root directory for the specified package.

        Notes:
            The presence of __init__.py is not required for preloads

        Args:
            package: Dot-delimited package root, e.g. 'cl.runtime'
        """
        package_tokens = package.split(".")
        package_tokens_len = len(package_tokens)
        source_root = cls.get_source_root(package)
        common_root = str(Path(source_root).parents[package_tokens_len - 1])
        if package_tokens[0] == "preloads":
            # Preloads directory is specified directly in module format
            return source_root
        else:
            # Look for tests package relative to source, return if exists
            preloads_root = os.path.normpath(os.path.join(common_root, "preloads", *package_tokens))
            if os.path.exists(preloads_root):
                return preloads_root
            else:
                return None

    @classmethod
    def get_static_dir(cls) -> str:
        """Directory for the static frontend files."""
        project_root = cls.get_project_root()
        return os.path.normpath(os.path.join(project_root, "static"))

    @classmethod
    def get_databases_dir(cls) -> str:
        """Path to databases directory under project root."""
        project_root = cls.get_project_root()
        db_dir = os.path.join(project_root, "databases")
        if not os.path.exists(db_dir):
            # Create the directory if does not exist
            os.makedirs(db_dir)
        return db_dir

    @classmethod
    def normalize_paths(cls, field_name: str, field_value: Iterable[str] | str | None) -> list[str]:
        """
        Convert to absolute path if path relative to the location of .env or Dynaconf file is specified
        and convert to list if single value is specified.
        """

        # Check that the argument is either None, a string or, an iterable
        if field_value is None:
            # Accept None and treat it as an empty list
            return []
        elif isinstance(field_value, str):
            paths = [field_value]
        elif hasattr(field_value, "__iter__"):
            paths = list(field_value)
        else:
            raise RuntimeError(
                f"Field '{field_name}' with value '{field_value}' in class '{typename(cls)}' "
                f"must be a string or an iterable of strings."
            )

        result = [cls.normalize_path(field_name, path) for path in paths]
        return result

    @classmethod
    def normalize_path(cls, field_name: str, field_value: str | None) -> str:
        """Convert to absolute path if path relative to the location of .env or Dynaconf file is specified."""

        if field_value is None or field_value == "":
            raise RuntimeError(f"Field '{field_name}' in class '{typename(cls)}' has an empty element.")
        elif isinstance(field_value, str):
            # Check that 'field_value' is a string
            result = field_value
        else:
            raise RuntimeError(
                f"Field '{field_name}' in class '{typename(cls)}' has an element "
                f"with type {type(field_value)} which is not a string."
            )

        if not os.path.isabs(result):
            project_root = cls.get_project_root()
            result = os.path.join(project_root, result)

        # Return as a normalized path string
        result = os.path.normpath(result)
        return result
