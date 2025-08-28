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
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.typename import typename
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
@final
class EnvSettings(Settings):
    """Settings for the naming and location of the app data."""

    env_id: str = required()
    """Unique environment identifier (does not apply inside pytest)."""

    env_kind: EnvKind = required()
    """Determines the default settings for multiuser access and data retention  (does not apply inside pytest)."""

    env_tenant: str = required()
    """Unique tenant identifier, tenants are isolated when sharing the same DB."""

    env_user: str | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Identifies the user."""

    env_shared: bool | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Data is shared by users if True and fully isolated by user if False (the user must be specified either way)."""

    env_packages: tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.env_kind is not None:
            # Field env_kind is specified in settings.yaml
            if isinstance(self.env_kind, str):
                # First, convert from snake_case to PascalCase (default for enums)
                env_kind_pascal_case = CaseUtil.snake_to_pascal_case(self.env_kind)
                self.env_kind = EnumUtil.from_str(
                    EnvKind,
                    env_kind_pascal_case,
                    field_name="env_kind",
                    class_name="EnvSettings",
                )
            elif not is_enum(self.env_kind):
                raise RuntimeError(
                    f"The value of env_kind={self.env_kind} in {typename(self)}\n"
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
                    f"env_id prefix for env_id={self.env_id}")

        if self.env_user is None:
            # Use the username reported by OS if not specified via Dynaconf
            os_user_id = getuser()
            self.env_user = os_user_id

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
