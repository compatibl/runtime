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
from typing import Tuple
from typing_extensions import final
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
@final
class EnvSettings(Settings):
    """Settings for the naming and location of the app data."""

    env_packages: Tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    env_kind: EnvKind | None = None  # TODO: Make required
    """Determines the default settings for multiuser access and data retention."""

    env_name: str | None = None
    """Identifies the environment or test."""

    env_user: str | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Identifies the user."""

    env_shared: bool | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Data is shared by users if True and fully isolated by user if false (the user must be specified either way)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Convert to tuple
        self.env_packages = SettingsUtil.to_str_tuple(self.env_packages)

        if self.env_kind is not None:
            # Convert from string to EnvKind enum if necessary
            if isinstance(self.env_kind, str):
                if self.env_kind.islower():
                    # Create enum after converting to uppercase if the string is in lowercase
                    if (item := self.env_kind.upper()) in EnvKind:
                        self.env_kind = EnvKind[item]  # noqa
                    else:
                        valid_items = "\n".join(item.name.lower() for item in EnvKind)
                        raise RuntimeError(
                            f"Enum EnvKind does not include the item {str(self.env_kind)}.\n"
                            f"Valid items are:\n{valid_items}\n"
                        )
                else:
                    raise RuntimeError(f"Invalid environment name {self.env_kind}, it should be lowercase.")
            elif not isinstance(self.env_kind, EnvKind):
                raise RuntimeError(f"The value of env should be a string or an instance of EnvKind.")

        if self.env_user is None:
            # Set default username if not specified in settings.yaml
            if (test_name_from_call_stack := QaUtil.get_test_name_from_call_stack_or_none()) is not None:
                # App user is test name from call stack if inside a test
                self.env_user = test_name_from_call_stack
            else:
                # Use the username reported by OS if not testing
                os_user_id = getuser()
                self.env_user = os_user_id

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
