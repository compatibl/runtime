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
from dataclasses import dataclass
from typing import Any, ClassVar
from dotenv import load_dotenv, find_dotenv, dotenv_values
from dynaconf import Dynaconf
from frozendict import frozendict
from typing_extensions import Self

from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_mapping_type
from cl.runtime.settings.env_kind import EnvKind

ENVVAR_PREFIX = "CL"
"""
Environment variable name is the global prefix (CL by default) followed by _ and then UPPER_CASE field name,
for example 'CL_SAMPLE_FIELD' for the field 'sample_field' in SampleSettings.
"""

SETTINGS_FILES_ENVVAR: str = f"{ENVVAR_PREFIX}_SETTINGS_FILES"
"""
Use to override the list of Dynaconf settings file names, must include file extensions but not the directory.
For package settings, underscore-delimited package name is added as prefix except for .secrets.
"""

SETTINGS_FILES_EXT_ENVVAR: str = f"{ENVVAR_PREFIX}_SETTINGS_FILES_EXT"
"""
Use to override the default Dynaconf settings files extension.
Do not include the leading dot. Defaults to 'yaml'.
"""

ENV_SWITCHER_ENVVAR: str = f"{ENVVAR_PREFIX}_SETTINGS_ENV"
"""Name of the envvar for switching between Dynaconf environments: production, staging, development and testing."""

ENV_KIND_ENVVAR: str = f"{ENVVAR_PREFIX}_ENV_KIND"
"""Name of the envvar for setting env_kind field."""

# Load dotenv first (priority order is environment variables first, then dotenv, then settings files)
load_dotenv()

# Override Dynaconf settings if inside a root test process
if QaUtil.is_test_root_process():
    # Switch to Dynaconf current_env=testing
    os.environ[ENV_SWITCHER_ENVVAR] = "testing"
    # Set env_kind to TEST
    os.environ[ENV_KIND_ENVVAR] = EnvKind.TEST.name


@dataclass(slots=True, kw_only=True)
class DynaconfLoader(BootstrapMixin):
    """
    Loads settings fields for the Dynaconf parameters including the settings dir and files.
    Envvars will override the data in the settings files.
    """

    package: str = required()
    """Package namespace for which the loader is created, affects settings directory and the list of settings files."""

    _envvar_prefix: str = required()
    """Environment variable prefix includes underscore-delimited package namespace if package is specified."""

    _settings_dir: str = required()
    """Absolute path to the settings directory."""

    _settings_filename: str = required()
    """Main settings filename without extension, additional settings filenames are formed by adding suffixes."""

    _settings_files_ext: str = required()
    """Settings files extension without the leading dot, does not apply to .secrets (defaults to 'yaml')."""

    _settings_files: tuple[str, ...] = required()
    """The complete list of Dynaconf settings files used by this loader."""

    _settings_dict: frozendict[str, Any] = required()
    """Dictionary of settings key-value pairs obtained from the Dynaconf object."""

    _package_dirs: frozendict[str, str] = required()
    """
    Ordered mapping of package source namespace to package directory relative to project root
    where dependent packages follow the packages they depend on.
    """

    __loader_dict: ClassVar[dict[str | None, Self]] = {}
    """Dictionary of DynaconfLoader instances indexed by the relative settings dir."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Absolute path to settings directory
        project_root = ProjectLayout.get_project_root()
        if self.package is not None:
            # Get Dynaconf loader for the project root first
            project_loader = DynaconfLoader.instance()
            # Use it to get the relative settings directory for the package
            rel_settings_dir = project_loader.get_package_dir(package=self.package)
            # Combine with project root to get the absolute path
            self._settings_dir = os.path.normpath(os.path.join(project_root, rel_settings_dir))
        else:
            # Settings directory is project root when package is not specified
            self._settings_dir = project_root

            # Set project loader to None if package is not specified
            project_loader = None

        if (settings_files := self.get_envvar_value(SETTINGS_FILES_ENVVAR)) is not None:
            # TODO(Claude): Settings files are specified, ensure they do not include directory path
            pass
        else:

            # Settings files extension may be modified by SETTINGS_FILES_EXT_ENVVAR environment variable
            self._settings_files_ext = self.get_envvar_value(SETTINGS_FILES_EXT_ENVVAR, "yaml")

            # Package-specific settings files and envvar prefix
            if self.package is not None:
                # Package-specific envvar prefix is underscore-delimited package namespace
                self._envvar_prefix = self.package.replace('.', '_').upper()

                # Settings filename without extension has package namespace prefix
                self._settings_filename = f"{self.package}.settings"
            else:
                # Package is not specified, do not use prefix
                self._envvar_prefix = ENVVAR_PREFIX

                # Package is not specified, do not use prefix
                self._settings_filename = "settings"

            # Baseline settings file
            settings_files = [f"{self._settings_filename}.{self._settings_files_ext}"]

            # Settings for the Dynaconf environment, add only if the environment is not None
            if (settings_env := self.get_envvar_value(ENV_SWITCHER_ENVVAR)) is not None:
                settings_files.append(f"{self._settings_filename}.{settings_env}.{self._settings_files_ext}")

            # Secrets file does not use package-specific prefix
            settings_files.append(f".secrets.{self._settings_files_ext}")

            # Local settings file overrides all others
            settings_files.append(f"{self._settings_filename}.local.{self._settings_files_ext}")

            # Make immutable
            self._settings_files = tuple(settings_files)

        # Combine settings file names with absolute settings directory path
        abs_settings_files = [os.path.normpath(os.path.join(self._settings_dir, x)) for x in self._settings_files]

        # Dynaconf settings in raw format (including system settings),
        # some keys may be strings instead of dictionaries or lists
        dynaconf = Dynaconf(
            environments=True,
            envvar_prefix=self._envvar_prefix,
            env_switcher=ENV_SWITCHER_ENVVAR,
            settings_files=abs_settings_files,
            dotenv_override=True,
        )

        # Extract user settings using as_dict(), then convert containers at all levels to dictionaries and lists
        # and convert root level keys to lowercase in case the settings are specified using envvars in uppercase format
        settings_dict = {k.lower(): v for k, v in dynaconf.as_dict().items()}

        # Populate selected fields in the package loader
        if self.package is not None:
            settings_dict["package_namespace"] = self.package
            settings_dict["package_dirs"] = project_loader.get_package_dirs()

        # Make immutable
        self._settings_dict = frozendict(settings_dict)

        if (package_dirs := self._settings_dict.get("package_dirs", None)) is not None:
            if not is_mapping_type(type(package_dirs)):
                raise RuntimeError(
                    "Field 'package_dirs' is specified but is not a mapping of package namespaces\n"
                    "to package root directories relative to project root."
                )

            for package_name, path in package_dirs.items():
                # Validate keys: valid dot-delimited package names
                # We check if each part of the dot-split string is a valid Python identifier
                if not all(part.isidentifier() for part in package_name.split(".")):
                    raise ValueError(
                        f"Invalid package name '{package_name}' in 'package_dirs' mapping in settings.\n"
                        "Keys must be valid dot-delimited package names."
                    )

                # Validate values: must be relative paths
                if os.path.isabs(path):
                    raise ValueError(
                        f"Invalid path '{path}' in 'package_dirs' mapping in settings.\n"
                        "Directories must be specified as relative paths to project root."
                    )

            self._package_dirs = frozendict(package_dirs)
        else:
            raise RuntimeError(
                "Field 'package_dirs' with the mapping of package namespaces to package root directories \n"
                "relative to project root to is required for multirepo layout."
            )

    @classmethod
    def instance(cls, *, package: str | None = None) -> Self:
        """
        Singleton instance of loader for the specified package, or for the project root if package is not specified.

        Args:
            package: Package namespace, e.g. 'cl.runtime' (optional)
        """
        # Check for an existing loader object, create if not found, otherwise return cached value
        if (result := cls.__loader_dict.get(package, None)) is None:
            result = DynaconfLoader(package=package).build()
            cls.__loader_dict[package] = result
        return result

    def get_settings_dir(self) -> str:
        """Absolute path to the settings directory."""
        return self._settings_dir

    def get_settings_files(self) -> tuple[str, ...]:
        """Dynaconf settings files for the specified package or for project root if package is not specified."""
        return self._settings_files

    def get_settings_dict(self) -> frozendict[str, Any]:
        """Dictionary of settings key-value pairs obtained from the Dynaconf object."""
        return self._settings_dict

    def get_package_dirs(self) -> frozendict[str, str]:
        """Get the mapping of package namespaces to package root directories relative to project root."""
        return self._package_dirs

    def get_package_dir(self, *, package: str) -> str:
        """Get package root directory relative to project root."""
        if (result := self._package_dirs.get(package, None)) is not None:
            return result
        else:
            raise RuntimeError(f"Field 'package_dirs' does not include the directory for package={package}")

    def get_sources_str(self, *, prefix: str) -> str:
        """Return the list of sources in the order of priority"""

        # Combine Dynaconf envvar prefix with field prefix
        field_prefix = f"{self._envvar_prefix}_{prefix.upper()}_"
        sources_list = [f"Environment variables with prefix '{field_prefix}'"]

        # Dotenv file source or message that it is not found
        if (env_file := find_dotenv()) != "":
            sources_list.append(f"Fields with prefix '{prefix}_' in .env file: {env_file}")

        # Dynaconf settings files
        settings_files_str = ", ".join(self.get_settings_files())
        sources_list.extend(f"Fields with prefix '{prefix}_' in settings files: {settings_files_str}")

        # Convert sources list to string
        sources_str ="\n".join(f"  - {x}" for x in sources_list)
        settings_dir_str = self.get_settings_dir()
        result =  f"Sources:\n{sources_str}\nSettings directory: {settings_dir_str}\n"
        return result


    @classmethod
    def get_envvar_value(cls, envvar: str, default: str | None = None) -> str | None:
        """
        Get value from an environment variable or .env file.

        Priority (highest to lowest):
        1. OS environment variable
        2. .env file
        3. Default value or None if not specified
        """
        return os.environ.get(envvar) or dotenv_values().get(envvar) or default
