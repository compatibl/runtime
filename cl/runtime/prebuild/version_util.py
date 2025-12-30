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
import importlib
from importlib.metadata import version, PackageNotFoundError
from frozendict import frozendict
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.version_settings import VersionSettings


class VersionUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    def get_version(cls, *, package: str, version_format_check: bool = True) -> str:
        """
        Get the version string from the specified package, raising an error
        if package is not found or does not define __version__.

        Args:
            package: Package namespace to get version for
            version_format_check: Validate version format if True
        """
        try:
            # Require that __version__ is defined in __init__.py of the package root rather than metadata
            module = importlib.import_module(package)
            ver = getattr(module, "__version__", None)
            if ver is not None:
                # Validate format if version_format_check is True
                if version_format_check:
                    cls.guard_version(ver=ver, package=package, raise_on_fail=True)
                return ver
            else:
                # Error if package is found but does not define __version__
                raise RuntimeError(
                    f"Required constant __version__ is not specified in root __init__.py of package {package}.\n"
                )
        except ModuleNotFoundError:
            # Error if root module of the package is not found
            raise RuntimeError(f"Cannot find package: {package}. Check sys.path")

    @classmethod
    def get_version_dict(cls, version_format_check: bool = True) -> frozendict[str, str]:
        """
        Get the version string from the specified package, raising an error if not found.

        Args:
            version_format_check: Validate version format if True.
        """
        env_settings = EnvSettings.instance()
        packages = env_settings.env_packages
        result = frozendict(
            {
                package: cls.get_version(package=package, version_format_check=version_format_check)
                for package in packages
            }
        )
        return result

    @classmethod
    def guard_version(cls, *, ver: str, package: str, raise_on_fail: bool = True) -> bool:
        """Check that the version string matches the CompatibL Platform CalVer convention."""

        # Error if version is not specified, even if version_format_check is False in settings
        if ver is None:
            raise RuntimeError(
                f"Required constant __version__ is not specified in root __init__.py of package {package}.\n"
            )

        # Exit early if version format check is False in settings
        version_settings = VersionSettings.instance()
        if not version_settings.version_format_check:
            return True

        # Evaluate each criterion and collect reasons for failure
        tokens = ver.split(".")
        reasons = []
        if len(tokens) != 3:
            reasons.append(f"Version must have exactly 3 dot-delimited tokens but has {len(tokens)}")
        if not all(p.isdigit() and (p == "0" or not p.startswith("0")) for p in tokens):
            reasons.append(f"All tokens must be numbers without leading zeros, except when the value is zero")
        if not (2000 <= int(tokens[0]) <= 2999):
            reasons.append(f"YYYY token {tokens[0]} is not between 2000 and 2999")
        if not (101 <= int(tokens[1]) <= 1231):
            reasons.append(f"MMDD token {tokens[1]} is not between 101 (Jan 1) and 1231 (Dec 31)")
        if not (0 <= int(tokens[2]) <= 2359):
            reasons.append(f"HHMM token {tokens[2]} is not between 0000 (midnight) and 2359 (12:59pm)")

        # Result is based on meeting all the criteria
        if not reasons:
            return True
        elif raise_on_fail:
            reasons_str = "\n".join("  - " + reason for reason in reasons)
            raise RuntimeError(
                f"Version string {ver} for package {package} does not follow\n"
                f"the YYYY.MMDD.HHMM CalVer format with no leading zeroes.\n"
                f"\nReasons:\n"
                f"{reasons_str}\n"
                f"\nExamples:\n"
                f" - 2003.501.0 for May 1, 2003 release at midnight\n"
                f" - 2003.1231.2359 for Dec 31, 2003 release at 11:59pm\n"
                f"\nTo disable, set version_format_check to False in settings.yaml.\n"
            )
        else:
            return False

    @classmethod
    def guard_version_dict(cls, ver_dict: frozendict[str, str], *, raise_on_fail: bool = True) -> bool:
        """
        Check that the version in each package follows the CompatibL Platform CalVer convention.
        """
        for package, ver in ver_dict.items():
            if not cls.guard_version(ver=ver, package=package, raise_on_fail=raise_on_fail):
                # Version check failed, return False if exception was not raised by guard_version
                return False
        # All versions passed the checks
        return True
