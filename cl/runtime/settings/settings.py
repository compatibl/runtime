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

from __future__ import annotations
import os
from abc import ABC
from dataclasses import MISSING
from dataclasses import dataclass
from typing import ClassVar
from typing import Self
from dotenv import find_dotenv
from dotenv import load_dotenv
from dynaconf import Dynaconf
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.typename import typename

# Load dotenv first (the priority order is envvars first, then dotenv, then settings.yaml and .secrets.yaml)
load_dotenv()

_process_timestamp = Timestamp.create()
"""Unique UUIDv7-based timestamp set during the Python process launch."""

# Override Dynaconf settings if inside a root test process
if QaUtil.is_test_root_process():
    # Switch to Dynaconf current_env=testing
    os.environ["CL_SETTINGS_ENV"] = "testing"
    # Set env_kind to TEST
    os.environ["CL_ENV_KIND"] = "TEST"

_DYNACONF_ALL_SETTINGS = Dynaconf(
    environments=True,
    envvar_prefix="CL",
    env_switcher="CL_SETTINGS_ENV",
    envvar="CL_SETTINGS_FILES",
    settings_files=[
        # Specify the exact path to prevent uncertainty associated with searching in multiple directories
        os.path.normpath(os.path.join(ProjectLayout.get_project_root(), "settings.yaml")),
        os.path.normpath(os.path.join(ProjectLayout.get_project_root(), ".secrets.yaml")),
    ],
    dotenv_override=True,
)
"""
Dynaconf settings in raw format (including system settings), some keys may be strings instead of dictionaries or lists.
"""

_DYNACONF_USER_SETTINGS = {k.lower(): v for k, v in _DYNACONF_ALL_SETTINGS.as_dict().items()}
"""
Extract user settings only using as_dict(), then convert containers at all levels to dictionaries and lists
and convert root level keys to lowercase in case the settings are specified using envvars in uppercase format
"""

_DYNACONF_ENVVAR_PREFIX = _DYNACONF_ALL_SETTINGS.envvar_prefix_for_dynaconf
"""Environment variable prefix for overriding dynaconf file settings."""

_DYNACONF_FILE_PATTERNS = _DYNACONF_ALL_SETTINGS.settings_file
"""List of Dynaconf settings file patterns or file paths."""

# Convert to list if a single string is specified
if isinstance(_DYNACONF_FILE_PATTERNS, str):
    _DYNACONF_FILE_PATTERNS = [_DYNACONF_FILE_PATTERNS]

_DYNACONF_LOADED_FILES = _DYNACONF_ALL_SETTINGS._loaded_files  # noqa
"""Loaded dynaconf settings files."""


@dataclass(slots=True, kw_only=True)
class Settings(BootstrapMixin, ABC):
    """
    Abstract base of settings classes.

    Notes:
      - Environment variable prefix is the global prefix (CL_ by default) followed by UPPER_CASE settings field name,
        for example 'CL_ENV_USER' for the field 'env_user' in EnvSettings
      - Dynaconf (settings.yaml) field is snake_case settings field name,
        for example 'env_user' for the field 'env_user' in EnvSettings
    """

    process_timestamp: ClassVar[str] = _process_timestamp
    """Unique UUIDv7-based timestamp set during the Python process launch."""

    __settings_dict: ClassVar[dict[type, Settings]] = {}
    """Dictionary of initialized settings objects indexed by the the settings class type."""

    @classmethod
    def get_prefix(cls) -> str:
        """
        Dynaconf fields will be filtered by 'prefix_' before being passed to the settings class constructor.
        Defaults to the class name converted to snake_case with 'Settings' suffix removed.

        Notes:
            - If this method provides an override of the default prefix, the returned prefix must be lowercase
            - and must not start or end with underscore (but may include underscore separators)
        """
        result = CaseUtil.pascal_to_snake_case(typename(cls)).removesuffix("_settings")
        result = result if result.endswith("_") else f"{result}_"
        return result

    @classmethod
    def get_dynaconf_env(cls) -> str:
        """
        Returns CL_SETTINGS_ENV converted to lowercase, defaults to 'development' if CL_SETTINGS_ENV is not set."""
        result = _DYNACONF_ALL_SETTINGS.current_env.lower()
        return result

    @classmethod
    def instance(cls) -> Self:
        """Return singleton instance."""

        # Check if cached value exists, load if not found
        if (result := cls.__settings_dict.get(cls, None)) is None:

            # Get and validate the field prefix to filter Dynaconf fields for this settings class
            prefix = cls.get_prefix()
            prefix_description = f"Dynaconf settings prefix '{prefix}' for {typename(cls)}"
            if prefix is None:
                raise RuntimeError(f"{prefix_description} is None.")
            if prefix == "":
                raise RuntimeError(f"{prefix_description} is an empty string.")
            if not prefix.islower():
                raise RuntimeError(f"{prefix_description} must be lowercase.")
            if prefix.startswith("_"):
                raise RuntimeError(f"{prefix_description} must not start with an underscore.")
            if not prefix.endswith("_"):
                raise RuntimeError(f"{prefix_description} must end with an underscore.")

            # Create a new dictionary of fields that start with 'prefix_'
            # This may include fields that are not specified in the settings class
            settings_dict = {k: v for k, v in _DYNACONF_USER_SETTINGS.items() if k.startswith(prefix)}

            slots = cls.get_field_names()
            slots_without_prefix = [slot for slot in slots if not slot.startswith(prefix)]
            if slots_without_prefix:
                slots_without_prefix_str = "\n".join(slots_without_prefix)
                message = (
                    f"The following fields in {typename(cls)} do not start with the prefix '{prefix}'\n"
                    f"returned by the '{typename(cls)}.get_prefix' method:\n{slots_without_prefix_str}"
                )
                raise RuntimeError(message)

            # List of required fields in cls (fields for which neither default nor default_factory is specified)
            required_fields = [
                name
                for name, field_info in cls.__dataclass_fields__.items()  # noqa
                if field_info.default is MISSING and field_info.default_factory is MISSING
            ]

            # Check for missing required fields
            missing_fields = [k for k in required_fields if k not in settings_dict]
            if missing_fields:
                # Combine the global Dynaconf envvar prefix with settings prefix
                envvar_prefix = f"{_DYNACONF_ENVVAR_PREFIX}_{prefix.upper()}"
                # Environment variables source
                sources_list = [f"Environment variables in uppercase with prefix '{envvar_prefix}'"]

                # Dotenv file source or message that it is not found
                if (env_file := find_dotenv()) != "":
                    env_file_name = env_file
                else:
                    env_file_name = "No .env file in default search path"
                sources_list.append(f"Dotenv file: {env_file_name}")

                # Dynaconf file source(s) or message that they are not found
                if _DYNACONF_LOADED_FILES:
                    dynaconf_file_list = _DYNACONF_LOADED_FILES
                else:
                    _dynaconf_file_patterns_str = ", ".join(_DYNACONF_FILE_PATTERNS)
                    dynaconf_file_list = [f"No {_dynaconf_file_patterns_str} file(s) in default search path."]
                sources_list.extend(f"Dynaconf file: {x}" for x in dynaconf_file_list)

                # Convert sources to string
                settings_sources_str = "\n".join(f"    - {x}" for x in sources_list)

                # List of missing required fields
                fields_error_msg_list = [
                    f"    - '{envvar_prefix}_{k.upper()}' (envvar/.env) or '{prefix}_{k}' (Dynaconf)"
                    for k in missing_fields
                ]
                fields_error_msg_str = "\n".join(fields_error_msg_list)

                # Raise exception with detailed information
                raise ValueError(
                    f"Required settings field(s) for {typename(cls)} not found:\n{fields_error_msg_str}\n"
                    f"Settings sources searched in the order of priority:\n{settings_sources_str}"
                )

            # TODO: Add a check for nested complex types in settings, if these are present deserialization will fail
            # TODO: Can custom deserializer that removes trailing and leading _ can be used without cyclic reference?
            result = cls(**settings_dict).build()  # noqa

            # Cache the result
            cls.__settings_dict[cls] = result

        return result
