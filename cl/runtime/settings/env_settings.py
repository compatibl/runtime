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

from dataclasses import dataclass
from getpass import getuser
from typing_extensions import final
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.enum_util import EnumUtil
from cl.runtime.primitive.identifier_util import IdentifierUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_enum_type
from cl.runtime.records.typename import typename
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
@final
class EnvSettings(Settings):
    """Settings for the naming and location of the app data."""

    env_id: str = required()
    """Unique environment identifier (does not apply inside pytest)."""

    env_kind: EnvKind = required()
    """Determines the default settings for multiuser access and data retention (does not apply inside pytest)."""

    env_user: str = required()
    """Identifies the application or test user (defaults to the OS user)."""

    env_tenant: str = required()
    """
    Unique tenant identifier, tenants are isolated when sharing the same DB.
    Defaults to env_user if not specified. The following variables can be used inside braces:
    
    - env_id
    - env_kind (converted to snake_case)
    - env_user
    """

    env_dir: str = required()
    """
    Defaults to project_resources if not specified. The following variables can be used inside braces:
    
    - project_root
    - project_resources
    - env_id
    - env_kind (converted to snake_case)
    - env_user
    - env_tenant
    """

    env_packages: tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.env_id is None:
            raise RuntimeError("Field env_id is missing in settings.yaml and env var is not set.")
        # Check the end result for safety
        IdentifierUtil.guard_valid_identifier(self.env_id)

        if self.env_kind is not None:
            # Field env_kind is specified in settings.yaml
            if isinstance(self.env_kind, str):
                # First, convert from snake_case to PascalCase (default for enums)
                env_kind_pascal_case = CaseUtil.snake_to_pascal_case(self.env_kind)
                self.env_kind = EnumUtil.from_str(
                    EnvKind,
                    env_kind_pascal_case,
                    field_name="env_kind",
                    type_name="EnvSettings",
                )
            elif not is_enum_type(type(self.env_kind)):
                raise RuntimeError(
                    f"The value of env_kind={self.env_kind} in {typename(type(self))}\n"
                    f"is not an EnvKind enum or a string."
                )
        else:
            # Field env_kind is not specified, use env_id prefix
            if self.env_id.startswith("prod_"):
                self.env_kind = EnvKind.PROD
            elif self.env_id.startswith("staging_"):
                self.env_kind = EnvKind.STAGING
            elif self.env_id.startswith("dev_"):
                self.env_kind = EnvKind.DEV
            elif self.env_id.startswith("temp_"):
                self.env_kind = EnvKind.TEMP
            elif self.env_id.startswith("test_"):
                self.env_kind = EnvKind.TEST
            else:
                raise RuntimeError(
                    f"Required field 'env_kind' is not set and cannot be determined from\n"
                    f"env_id prefix for env_id={self.env_id}"
                )

        if self.env_user is None:
            # Set to the username reported by OS if not specified via Dynaconf
            self.env_user = getuser()
        # Check the end result for safety
        IdentifierUtil.guard_valid_identifier(self.env_user)

        if self.env_tenant is None:
            # Set env_tenant to env_user if not specified via Dynaconf
            self.env_tenant = self.env_user
        else:
            # Check for safety before substitution
            IdentifierUtil.guard_valid_identifier(self.env_tenant, allow_braces=True)
            # Perform variable substitution
            env_tenant_vars = {
                "env_id": self.env_id,
                "env_kind": CaseUtil.upper_to_snake_case(self.env_kind.name),
                "env_user": self.env_user,
            }
            self.env_tenant = self.env_tenant.format(**env_tenant_vars)

        # Check the end result for safety
        IdentifierUtil.guard_valid_identifier(self.env_tenant)

        if self.env_dir is None:
            # Default if not specified via Dynaconf
            self.env_dir = ProjectLayout.get_resources_root()
        else:
            # Check for safety before substitution
            IdentifierUtil.guard_valid_identifier(self.env_dir, allow_braces=True, allow_directory_separators=True)
            # Perform variable substitution
            env_dir_vars = {
                "project_root": ProjectLayout.get_project_root(),
                "project_resources": ProjectLayout.get_resources_root(),  # TODO: Update after ProjectLayout changes
                "env_id": self.env_id,
                "env_kind": CaseUtil.upper_to_snake_case(self.env_kind.name),
                "env_user": self.env_user,
                "env_tenant": self.env_tenant,
            }
            self.env_dir = self.env_dir.format(**env_dir_vars)

        # Check the end result for safety
        IdentifierUtil.guard_valid_identifier(self.env_dir, allow_directory_separators=True)

        # Convert the list of packages to tuple
        self.env_packages = SettingsUtil.to_str_tuple(self.env_packages)

    def cleanup_before(self) -> bool:
        """Cleanup deployment data (except logs) before each run if true."""
        if self.env_kind in (EnvKind.PROD, EnvKind.STAGING):
            return False
        elif self.env_kind in (EnvKind.DEV, EnvKind.TEMP):
            return True
        else:
            raise ErrorUtil.enum_value_error(self.env_kind, EnvKind)

    def cleanup_after(self) -> bool:
        """Cleanup deployment data (except logs) after each run if true."""
        if self.env_kind in (EnvKind.PROD, EnvKind.STAGING, EnvKind.DEV):
            return False
        elif self.env_kind == EnvKind.TEMP:
            return True
        else:
            raise ErrorUtil.enum_value_error(self.env_kind, EnvKind)
