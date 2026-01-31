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
from typing import Mapping
from typing import Sequence
from dotenv import load_dotenv, find_dotenv
from dynaconf import Dynaconf
from frozendict import frozendict
from requests.packages import package
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

SETTINGS_FILES_ENVVAR: str = "CL_SETTINGS_FILES"
"""Name of the envvar to override the settings files provided to Dynaconf constructor."""

ENV_SWITCHER_ENVVAR: str = "CL_SETTINGS_ENV"
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

    _settings_dir: str = required()
    """Absolute path to the settings directory."""

    _settings_files: tuple[str, ...] = required()
    """Dynaconf settings files for the specified package or for project root if package is not specified."""

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

        if self.package is not None:
            # Get Dynaconf loader for the project root first
            project_loader = DynaconfLoader.instance()
            # Use it to get settings directory for the package
            rel_settings_dir = project_loader.get_package_dir(package=self.package)
        else:
            # Settings directory is project root when package is None
            rel_settings_dir = ProjectLayout.get_project_root()

        # Absolute path to the settings directory
        self._settings_dir = ProjectLayout.get_project_root()
        if rel_settings_dir is not None:
            self._settings_dir = os.path.normpath(os.path.join(self._settings_dir, rel_settings_dir))

        # Package-specific settings file
        if self.package is not None:
            # Begin from the settings file for the individual package with the lowest priority
            settings_files = [f"{self.package}.yaml"]
        else:
            # No additional settings files when package is None
            settings_files = []

        # Project-wide settings files
        settings_files.append("settings.yaml")  # Baseline
        if (settings_env := os.environ.get(ENV_SWITCHER_ENVVAR)) is not None:
            # Settings for the Dynaconf environment, add only if the environment is not None
            settings_files.append(f"settings.{settings_env}.yaml")
        settings_files.append(".secrets.yaml")  # Secrets
        settings_files.append("settings.local.yaml")  # Local settings file overrides all other settings
        self._settings_files = tuple(settings_files)

        # Combine settings file names with absolute settings directory path
        abs_settings_files = [os.path.normpath(os.path.join(self._settings_dir, x)) for x in self._settings_files]

        # Dynaconf settings in raw format (including system settings),
        # some keys may be strings instead of dictionaries or lists
        dynaconf = Dynaconf(
            environments=True,
            envvar_prefix=ENVVAR_PREFIX,
            env_switcher=ENV_SWITCHER_ENVVAR,
            envvar=SETTINGS_FILES_ENVVAR,
            settings_files=abs_settings_files,
            dotenv_override=True,
        )

        # Set package_namespace field using the package parameter
        dynaconf["package_namespace"] = self.package

        # Extract user settings using as_dict(), then convert containers at all levels to dictionaries and lists
        # and convert root level keys to lowercase in case the settings are specified using envvars in uppercase format
        self._settings_dict = frozendict({k.lower(): v for k, v in dynaconf.as_dict().items()})

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

    def get_package_dir(self, *, package: str) -> str:
        """Get package root directory relative to project root."""
        if (result := self._package_dirs.get(package, None)) is not None:
            return result
        else:
            raise RuntimeError(f"Field 'package_dirs' does not include the directory for package={package}")

    def get_sources_str(self, *, prefix: str) -> str:
        """Return the list of sources in the order of priority"""

        # Combine the global Dynaconf envvar prefix with settings prefix
        envvar_prefix = f"{ENVVAR_PREFIX}_{prefix.upper()}_"
        sources_list = [f"Envvars with prefix '{envvar_prefix}'"]

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
