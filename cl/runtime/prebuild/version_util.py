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
import importlib.util
import re

# Pattern to find version in setup.py file
_SETUP_PY_VERSION_RE = r"""(?s)(?!^\s*#)\s*setuptools\.setup\s*\(.*?\bversion\s*=\s*(['"])(?P<version>[^'"]+)\1"""

# Pattern to find version in _version.py file
_VERSION_PY_VERSION_RE = r"""(?m)^\s*(?!#)\s*__version__\s*=\s*(['"])(?P<version>[^'"]+)\1"""

# Pattern to find version in pyproject.toml file
_PYPROJECT_TOML_VERSION_RE = r"""(?ms)^\[project\]\s*.*?^\s*(?!#)\s*version\s*=\s*(['"])(?P<version>[^'"]+)\1"""


class VersionUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    def guard_package_version(cls, package: str, *, raise_on_fail: bool = True) -> bool:
        """
        Check that the versions in package are the same and matches the CompatibL Platform CalVer format.
        """
        try:
            spec = importlib.util.find_spec(package)
        except ImportError as error:
            raise RuntimeError(f"Cannot import module: {error.name}. Check sys.path")

        package_path = os.path.dirname(spec.origin)

        # Get versions from different possible places in the package
        setup_py_version = cls.find_version_in_setup_py(package_path)
        version_py_version = cls.find_version_in_version_py(package_path)
        pyproject_toml_version = cls.find_version_in_pyproject_toml(package_path)

        # Verify that versions match each other
        if setup_py_version == version_py_version == pyproject_toml_version:
            # Valid if all versions are the same
            is_valid = True
        elif setup_py_version is None and version_py_version == pyproject_toml_version:
            # setup_py_version is optional, so it is valid if setup_py_version is None and
            # all other versions are the same
            is_valid = True
        else:
            # Not valid in all other cases
            is_valid = False

        if not is_valid:
            if raise_on_fail:
                raise RuntimeError(
                    f"Versions in package {package} is not valid.\n"
                    f"The following versions were found:\n"
                    f" - In pyproject.toml file: {pyproject_toml_version}\n"
                    f" - In _version.py file: {version_py_version}\n"
                    f" - In setup.py file [optional]: {setup_py_version}\n"
                )
            else:
                return False

        if all((setup_py_version is None, pyproject_toml_version is None, version_py_version is None)):
            return True
        else:
            return cls.guard_version_string(pyproject_toml_version, raise_on_fail=raise_on_fail)

    @classmethod
    def guard_version_string(cls, ver: str, *, raise_on_fail: bool = True) -> bool:
        """Check that the version string matches the CompatibL Platform CalVer format."""
        tokens = ver.split(".")
        is_valid = (
            len(tokens) == 3 and
            all(p.isdigit() and (p == '0' or not p.startswith('0')) for p in tokens)
            and 2025 <= int(tokens[0]) <= 2999  # Four-digit year from 2025 to 2999
            and 101 <= int(tokens[1]) <= 1231  # Month and day combined from 101 (Jan 1) to 1231 (Dec 31)
        )
        if is_valid:
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Version string {ver} does not follow the CompatibL Platform\n"
                               f"CalVar convention of YYYY.MDD.PATCH. Examples:\n"
                               f" - 2023.101.0 for Jan 1, 2023 release\n"
                               f" - 2023.501.1 for patch 1 to May 1, 2023 release\n")
        else:
            return False

    @classmethod
    def _find_version_in_file(cls, file_path: str, version_re: str) -> str | None:
        """
        Find version in file_path using version_re.
        Return None if file doesn't exist or version is not found.
        Raise RuntimeError if found more than one version.
        """
        if not os.path.isfile(file_path):
            # Return None if file not found
            return None

        version_re = re.compile(version_re)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        matches = version_re.findall(content)

        if not matches:
            return None

        if len(matches) > 1:
            versions = [m[1] for m in matches]
            raise RuntimeError(f"Multiple versions found in {file_path}: {versions}")

        # matches[0] = (quote, version)
        return matches[0][1]

    @classmethod
    def find_version_in_setup_py(cls, package_path: str) -> str | None:
        """Find exactly one version="..." in setup.py."""
        setup_py_path = os.path.join(os.path.dirname(os.path.dirname(package_path)), "setup.py")
        return cls._find_version_in_file(setup_py_path, _SETUP_PY_VERSION_RE)

    @classmethod
    def find_version_in_version_py(cls, package_path: str) -> str | None:
        """Find exactly one __version__ = "..." in _version.py."""
        version_py_path = os.path.join(package_path, "_version.py")
        return cls._find_version_in_file(version_py_path, _VERSION_PY_VERSION_RE)

    @classmethod
    def find_version_in_pyproject_toml(cls, package_path: str) -> str | None:
        """Find exactly one version = "..." in pyproject.toml."""
        pyproject_toml_path = os.path.join(os.path.dirname(os.path.dirname(package_path)), "pyproject.toml")
        return cls._find_version_in_file(pyproject_toml_path, _PYPROJECT_TOML_VERSION_RE)