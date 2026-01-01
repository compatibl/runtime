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

from cl.runtime.prebuild.import_util import ImportUtil
from cl.runtime.settings.version_settings import VersionSettings


class VersionUtil:
    """Helper class for working with copyright headers and files."""

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
        Check that the version string is present. If version_format_check is true,
        also check matches the convention specified in settings.

        Args:
            version: Version string
            module: Module name for checking the version format and error messages
            raise_on_fail: If the check fails, return False or raise an error depending on raise_on_fail
        """

        # Error if version is not specified, even if version_format_check is False in settings
        if version is None:
            raise RuntimeError(
                f"Required constant __version__ is not specified in root __init__.py of module {module}.\n"
            )

        # Exit early if version format check is False in settings
        version_settings = VersionSettings.instance()
        if not version_settings.version_format_check:
            return True

        # Evaluate each criterion and collect reasons for failure
        tokens = version.split(".")
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
                f"Version string {version} for module {module} does not follow\n"
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
    def guard_version_dict(cls, version_dict: frozendict[str, str], *, raise_on_fail: bool = True) -> bool:
        """
        Check that each version in the dict is not empty or None. If version_format_check is true,
        also check matches the convention specified in settings.
        """
        for module, version in version_dict.items():
            if not cls.guard_module_version(version=version, module=module, raise_on_fail=raise_on_fail):
                # Version check failed, return False if exception was not raised by guard_version
                return False
        # All versions passed the checks
        return True
