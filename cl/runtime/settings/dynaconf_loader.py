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
from typing import Sequence, Any, Mapping, Self
from dotenv import load_dotenv
from dynaconf import Dynaconf
from frozendict import frozendict

from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.for_dataclasses.extensions import required
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
    os.environ["CL_SETTINGS_ENV"] = "testing"
    # Set env_kind to TEST
    os.environ["CL_ENV_KIND"] = "TEST"

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

    settings_dir: str = required()
    """Directory where Dynaconf settings files are located."""

    settings_files: Sequence[str] = required()
    """Names of the Dynaconf settings files to load."""

    loaded_files: Sequence[str] = required()
    """Names of the actually loaded Dynaconf settings files."""

    dynaconf_env: str = required()
    """Current Dynaconf environment."""

    fields_dict: Mapping[str, Any] = required()
    """Dictionary of settings field values indexed by field name."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.settings_files is None:
            self.settings_files = (
                "settings.yaml", # Launch configuration
                "project.yaml", # Build configuration
                ".secrets.yaml",  # Secrets
            )

        # Absolute paths to settings directory
        settings_dir_path = ProjectLayout.get_project_root()
        if self.settings_dir is not None:
            settings_dir_path = os.path.normpath(os.path.join(settings_dir_path, self.settings_dir))

        # Dynaconf settings in raw format (including system settings),
        # some keys may be strings instead of dictionaries or lists
        dynaconf = Dynaconf(
            environments=True,
            envvar_prefix=ENVVAR_PREFIX,
            env_switcher=ENV_SWITCHER_ENVVAR,
            envvar=SETTINGS_FILES_ENVVAR,
            settings_files=[os.path.normpath(os.path.join(settings_dir_path, x)) for x in self.settings_files],
            dotenv_override=True,
        )

        # Actually loaded Dynaconf settings files
        self.loaded_files = dynaconf._loaded_files  # noqa

        # Current Dynaconf environment
        self.dynaconf_env = str(dynaconf.current_env.lower())

        # Extract user settings using as_dict(), then convert containers at all levels to dictionaries and lists
        # and convert root level keys to lowercase in case the settings are specified using envvars in uppercase format
        self.fields_dict = frozendict({k.lower(): v for k, v in dynaconf.as_dict().items()})

    def get_fields_dict(self, field_names: Sequence[str]) -> Mapping[str, Any]:
        """Return a dictionary of filed name-value pairs limited to the specified field names."""
        return {k: self.fields_dict[k] for k in field_names if k in self.fields_dict}
