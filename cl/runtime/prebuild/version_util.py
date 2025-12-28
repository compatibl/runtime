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

from importlib.util import find_spec
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.version_settings import VersionSettings


class VersionUtil:
    """Helper class for working with copyright headers and files."""

    @classmethod
    def guard_versions(cls, raise_on_fail: bool = True) -> bool:
        """
        Check that the version in each package follows the CompatibL Platform CalVer convention.
        """
        env_settings = EnvSettings.instance()
        env_packages = env_settings.env_packages
        for env_package in env_packages:
            try:
                # Import the package
                package_spec = find_spec(env_package)
                # Load __version__ from the package __init__.py
                if package_spec and package_spec.loader:
                    module = package_spec.loader.load_module()
                    version = getattr(module, "__version__", None)
                    if version is not None:
                        if not cls.guard_version(version=version, package=env_package, raise_on_fail=raise_on_fail):
                            # Version check failed, return False if exception was not raised by guard_version
                            return False
                else:
                    raise RuntimeError(f"Cannot find module: {env_package}. Check sys.path")
            except ImportError as error:
                raise RuntimeError(f"Cannot import module: {error.name}. Check sys.path")

        # All versions passed the checks
        return True

    @classmethod
    def guard_version(cls, *, version: str, package: str, raise_on_fail: bool = True) -> bool:
        """Check that the version string matches the CompatibL Platform CalVer convention."""

        # Exit early if version format check is disabled
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
                f"Version string {version} for package {package} does not follow\n"
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
