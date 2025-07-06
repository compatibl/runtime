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
from abc import abstractmethod
from dataclasses import MISSING
from dataclasses import dataclass
from typing import ClassVar
from typing import Dict
from dotenv import find_dotenv
from dotenv import load_dotenv
from dynaconf import Dynaconf
from typing_extensions import Self
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.project_settings import SETTINGS_FILES_ENVVAR
from cl.runtime.settings.project_settings import ProjectSettings

# Load dotenv first (the priority order is envvars first, then dotenv, then settings.yaml and .secrets.yaml)
load_dotenv()

_process_timestamp = Timestamp.create()
"""Unique UUIDv7-based timestamp set during the Python process launch."""

# True if we are inside a test process, use ProcessSettings.is_testing() to also detect inside child processes
is_test_process = QaUtil.inspect_stack_for_test_module_pattern()

# Select Dynaconf test environment when invoked from the pytest or UnitTest test runner.
# Other runners not detected automatically, in which case the Dynaconf environment must be
# configured in settings explicitly.
if is_test_process:
    os.environ["CL_SETTINGS_ENV"] = "test"

_all_settings = Dynaconf(
    environments=True,
    envvar_prefix="CL",
    env_switcher="CL_SETTINGS_ENV",
    envvar=SETTINGS_FILES_ENVVAR,
    settings_files=[
        # Specify the exact path to prevent uncertainty associated with searching in multiple directories
        os.path.normpath(os.path.join(ProjectSettings.get_project_root(), "settings.yaml")),
        os.path.normpath(os.path.join(ProjectSettings.get_project_root(), ".secrets.yaml")),
    ],
    dotenv_override=True,
)
"""
Dynaconf settings in raw format (including system settings), some keys may be strings instead of dictionaries or lists.
"""

_user_settings = {k.lower(): v for k, v in _all_settings.as_dict().items()}
"""
Extract user settings only using as_dict(), then convert containers at all levels to dictionaries and lists
and convert root level keys to lowercase in case the settings are specified using envvars in uppercase format
"""

_dynaconf_envvar_prefix = _all_settings.envvar_prefix_for_dynaconf
"""Environment variable prefix for overriding dynaconf file settings."""

_dynaconf_file_patterns = _all_settings.settings_file
"""List of Dynaconf settings file patterns or file paths."""

# Convert to list if a single string is specified
if isinstance(_dynaconf_file_patterns, str):
    _dynaconf_file_patterns = [_dynaconf_file_patterns]

_dynaconf_loaded_files = _all_settings._loaded_files  # noqa
"""Loaded dynaconf settings files."""


@dataclass(slots=True, kw_only=True)
class Settings(DataMixin, ABC):
    """
    Abstract base of settings classes.

    Notes:
      - Environment variable prefix is the global prefix (CL_ by default) followed
        by UPPER_CASE settings class name with suffix '_SETTINGS' removed,
        for example 'CL_APP_USER' for the field 'user' in AppSettings.
      - Dynaconf (settings.yaml) prefix is snake_case settings class name with suffix '_settings'
        removed, for example 'app_user' for the field 'user' in AppSettings.
      - Use CL_APP_SETTINGS_TYPE environment variable or app_settings_type Dynaconf (settings.yaml) key
        to specify a settings type derived from AppSettings.
    """

    process_timestamp: ClassVar[str] = _process_timestamp
    """Unique UUIDv7-based timestamp set during the Python process launch."""

    is_inside_test: ClassVar[bool] = is_test_process
    """True if we are inside a test."""

    __settings_dict: ClassVar[Dict[type, Settings]] = {}
    """Dictionary of initialized settings objects indexed by the the settings class type."""

    @classmethod
    def instance(cls) -> Self:
        """Return singleton instance."""

        # Check that the method is not invoked on the Settings base class
        if cls == Settings:
            raise RuntimeError(
                "Class method instance() can be invoked on final Settings classes but not the Settings base class.")

        # All settings classes must be final
        if not hasattr(cls, '__final__'):
            raise RuntimeError(
                f"Settings class {TypeUtil.name(cls)} is not marked as final, or for Python version < 3.11 the @final"
                f"decorator was imported from typing rather than typing_extensions.")

        # Check if cached value exists, load if not found
        if (result := cls.__settings_dict.get(cls, None)) is None:

            # Settings class name determines the prefix used to filter dynaconf fields
            settings_type_name = TypeUtil.name(cls)
            if settings_type_name.endswith("Settings"):
                prefix = CaseUtil.pascal_to_snake_case(settings_type_name.removesuffix("Settings"))

            # Validate prefix
            prefix_description = f"Dynaconf settings prefix '{prefix}' returned by '{TypeUtil.name(cls)}.get_prefix()'"
            if prefix is None:
                raise RuntimeError(f"{prefix_description} is None.")
            if prefix == "":
                raise RuntimeError(f"{prefix_description} is an empty string.")
            if not prefix.islower():
                raise RuntimeError(f"{prefix_description} must be lowercase.")
            if prefix.startswith("_"):
                raise RuntimeError(f"{prefix_description} must not start with an underscore.")
            if prefix.endswith("_"):
                raise RuntimeError(f"{prefix_description} must not end with an underscore.")

            # Filter user settings by 'prefix_' and create a new dictionary where prefix is removed from keys
            # This will include fields that are not specified in the settings class
            p = prefix + "_"
            settings_dict = {k[len(p):]: v for k, v in _user_settings.items() if k.startswith(p)}

            # List of required fields in cls (fields for which neither default nor default_factory is specified)
            required_fields = [
                name
                for name, field_info in cls.__dataclass_fields__.items()  # noqa
                if field_info.default is MISSING and field_info.default_factory is MISSING
            ]

            # Check for missing required fields
            missing_fields = [k for k in required_fields if k not in settings_dict]
            if missing_fields:
                # Combine the global Dynaconf envvar prefix with settings prefix in uppercase
                envvar_prefix = f"{_dynaconf_envvar_prefix}_{prefix.upper()}"
                dynaconf_msg = f"(in lowercase with prefix '{prefix}_')"
                envvar_msg = f"(in uppercase with prefix '{envvar_prefix}_')"

                # Environment variables
                sources_list = [f"Environment variables {envvar_msg}"]

                # Dotenv file or message that it is not found
                if (env_file := find_dotenv()) != "":
                    env_file_name = env_file
                else:
                    env_file_name = "No .env file in default search path"
                sources_list.append(f"Dotenv file {envvar_msg}: {env_file_name}")

                # Dynaconf file(s) or message that they are not found
                if _dynaconf_loaded_files:
                    dynaconf_file_list = _dynaconf_loaded_files
                else:
                    _dynaconf_file_patterns_str = ", ".join(_dynaconf_file_patterns)
                    dynaconf_file_list = [f"No {_dynaconf_file_patterns_str} file(s) in default search path."]
                sources_list.extend(f"Dynaconf file {dynaconf_msg}: {x}" for x in dynaconf_file_list)

                # Convert to string
                settings_sources_str = "\n".join(f"    - {x}" for x in sources_list)

                # List of missing required fields
                fields_error_msg_list = [
                    f"    - '{envvar_prefix}_{k.upper()}' (envvar/.env) or '{prefix}_{k}' (Dynaconf)"
                    for k in missing_fields
                ]
                fields_error_msg_str = "\n".join(fields_error_msg_list)

                # Raise exception with detailed information
                raise ValueError(
                    f"Required settings field(s) for {TypeUtil.name(cls)} not found:\n{fields_error_msg_str}\n"
                    f"Settings sources searched in the order of priority:\n{settings_sources_str}"
                )

            # TODO: Add a check for nested complex types in settings, if these are present deserialization will fail
            # TODO: Can custom deserializer that removes trailing and leading _ can be used without cyclic reference?
            result = cls(**settings_dict).build()

            # Cache the result
            cls.__settings_dict[cls] = result

        return result
