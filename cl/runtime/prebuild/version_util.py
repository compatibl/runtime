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
from typing import Sequence

from frozendict import frozendict
from memoization import cached

from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.prebuild.import_util import ImportUtil
from cl.runtime.prebuild.version_format import VersionFormat
from cl.runtime.settings.version_settings import VersionSettings


class VersionUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    @cached
    def get_module_version_format_or_none(cls, *, module: str) -> VersionFormat | None:
        """Get the module version enum for the specified module."""
        version_settings = VersionSettings.instance()

        # Check if specified for the specific module first
        result = None
        if (format_dict := version_settings.version_format) is not None:
            result = format_dict.get(module, None)

        # If the dictionary is not specified or it does not include the module, check for the default version
        if result is None:
            result = version_settings.version_format_default

        # The result will be None if neither is specified
        return result

    @classmethod
    @cached
    def get_module_version(cls, *, module: str) -> str:
        """Get the version string for the specified module."""
        module_obj = ImportUtil.get_module(module=module)
        try:
            return module_obj.__version__
        except AttributeError:
            raise RuntimeError(f"Module {module} does not import or define a __version__ variable.")

    @classmethod
    @cached
    def get_version_dict(cls, *, packages: Sequence[str]) -> frozendict[str, str]:
        """Get the version string from the specified package, raising an error if not found."""
        modules = ImportUtil.get_modules(packages=packages)
        result = frozendict(
            {
                module.__name__: version
                for module in modules
                if (version := getattr(module, "__version__", None)) is not None
            }
        )
        return result

    @classmethod
    def guard_module_version(cls, *, version: str, module: str, raise_on_fail: bool = True) -> bool:
        """
        Check that the version string is present. If version_format is specified in settings.yaml for the module
        or version_format_default is set, also check matches the convention specified in settings.

        Args:
            version: Version string
            module: Module name for checking the version format and error messages
            raise_on_fail: If the check fails, return False or raise an error depending on raise_on_fail
        """

        # Error if version is not specified, even if version_format is not specified in settings.yaml
        # for the modul and version_format_default is not set
        if version is None:
            raise RuntimeError(
                f"Required constant __version__ is not specified in root __init__.py of module {module}.\n"
            )

        # Get version format from settings and perform validation
        version_format = cls.get_module_version_format_or_none(module=module)

        # Exit early if None
        if version_format is None:
            return True

        tokens = version.split(".")
        reasons = []
        if version_format == VersionFormat.SEM_VER:
            if len(tokens) != 3:
                reasons.append(f"SemVer must have exactly 3 dot-delimited tokens but has {len(tokens)}")
            if not all(p.isdigit() and (p == "0" or not p.startswith("0")) for p in tokens):
                reasons.append(f"SemVer tokens must be numbers without leading zeros, except when they are zero")
        elif version_format == VersionFormat.CAL_VER:
            if len(tokens) != 3:
                reasons.append(f"CalVer must have exactly 3 dot-delimited tokens but has {len(tokens)}")
            if not all(p.isdigit() and (p == "0" or not p.startswith("0")) for p in tokens):
                reasons.append(f"CalVer tokens must be numbers without leading zeros, except when the value is zero")
            if version_format == VersionFormat.CAL_VER:
                if not (2000 <= int(tokens[0]) <= 2999):
                    reasons.append(f"First CalVer token {tokens[0]} is not YYYY between 2000 and 2999")
                if not (101 <= int(tokens[1]) <= 1231):
                    reasons.append(f"Second CalVer token {tokens[1]} is not MMDD between 101 (Jan 1) and 1231 (Dec 31)")
                if not (0 <= int(tokens[2]) <= 2359):
                    reasons.append(
                        f"Third CalVer token {tokens[2]} is not HHMM between 0000 (midnight) and 2359 (12:59pm)"
                    )
        else:
            ErrorUtil.enum_value_error(version_format, VersionFormat)  # noqa

        # Result is based on meeting all the criteria
        if not reasons:
            return True
        elif raise_on_fail:
            reasons_str = "\n".join("  - " + reason for reason in reasons)
            if version_format == VersionFormat.SEM_VER:
                raise RuntimeError(
                    f"Version string {version} for module {module} does not follow\n"
                    f"SemVer MAJOR.MINOR.PATCH format with no leading zeroes.\n"
                    f"\nReasons:\n"
                    f"{reasons_str}\n\n"
                    f"To disable version format check, clear version_format and version_format_default\n"
                    f"fields in settings.yaml.\n"
                )
            elif version_format == VersionFormat.CAL_VER:
                raise RuntimeError(
                    f"Version string {version} for module {module} does not follow\n"
                    f"CalVer YYYY.MMDD.HHMM format with no leading zeroes.\n"
                    f"\nReasons:\n"
                    f"{reasons_str}\n"
                    f"\nExamples:\n"
                    f" - 2003.501.0 for May 1, 2003 release at midnight\n"
                    f" - 2003.1231.2359 for Dec 31, 2003 release at 11:59pm\n\n"
                    f"To disable version format check, clear version_format and version_format_default\n"
                    f"fields in settings.yaml.\n"
                )
            else:
                ErrorUtil.enum_value_error(version_format, VersionFormat)  # noqa
        else:
            return False

    @classmethod
    def guard_version_dict(cls, version_dict: frozendict[str, str], *, raise_on_fail: bool = True) -> bool:
        """
        Check that each version in the dict is not empty or None. If version_format is specified in settings.yaml
        for the module or version_format_default is set, also check matches the convention specified in settings.
        """
        for module, version in version_dict.items():
            if not cls.guard_module_version(version=version, module=module, raise_on_fail=raise_on_fail):
                # Version check failed, return False if exception was not raised by guard_version
                return False
        # All versions passed the checks
        return True
