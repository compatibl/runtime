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
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.app_env import AppEnv
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class AppSettings(Settings):
    """Settings for the naming and location of the app data."""

    app_packages: Tuple[str, ...] = required()
    """List of packages to load in dot-delimited format, for example 'cl.runtime' or 'stubs.cl.runtime'."""

    app_env: AppEnv | None = None  # TODO: Make required
    """Determines the default settings for multiuser access and data retention."""

    app_name: str | None = None
    """Identifies the application or test."""

    app_user: str | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Identifies the application or test user."""

    app_user_scoped: bool | None = None  # TODO: Determine if this should be here or in UserContext, keep one
    """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Convert to tuple
        if self.app_packages is None:
            raise RuntimeError(f"No packages are specified in {TypeUtil.name(self)}, specify at least one.")
        elif is_sequence(self.app_packages):
            # Convert sequence to tuple
            self.app_packages = tuple(self.app_packages)
        elif isinstance(self.app_packages, str):
            # Deserialize from string in comma-delimited format
            self.app_packages = tuple(token.strip() for token in self.app_packages.split(","))
        else:
            raise RuntimeError(f"Field '{TypeUtil.name(self)}.packages' must be a string or an iterable of strings.")

        # Check that each element is a string and is not empty
        package_errors = [
            (
                f"- Element at index {index} of field '{TypeUtil.name(self)}.packages is not a string:\n"
                f"  Value: {element} Type: {TypeUtil.name(element)})\n"
                if not isinstance(element, str)
                else f"- Element at index {index} of field '{TypeUtil.name(self)} is an empty string.\n"
            )
            for index, element in enumerate(self.app_packages)
            if not isinstance(element, str) or element == ""
        ]
        if package_errors:
            raise ValueError("\n".join(package_errors))

        if self.app_env is not None:
            # Convert from string to AppEnv enum if necessary
            if isinstance(self.app_env, str):
                if self.app_env.islower():
                    # Create enum after converting to uppercase if the string is in lowercase
                    if (item := self.app_env.upper()) in AppEnv:
                        self.app_env = AppEnv[item]  # noqa
                    else:
                        valid_items = "\n".join(item.name.lower() for item in AppEnv)
                        raise RuntimeError(
                            f"Enum AppEnv does not include the item {str(self.app_env)}.\n"
                            f"Valid items are:\n{valid_items}\n"
                        )
                else:
                    raise RuntimeError(f"Invalid environment name {self.app_env}, it should be lowercase.")
            elif not isinstance(self.app_env, AppEnv):
                raise RuntimeError(f"The value of env should be a string or an instance of AppEnv.")

        if self.app_user is None:
            # Set default username if not specified in settings.yaml
            if (test_name_from_call_stack := QaUtil.get_test_name_from_call_stack_or_none()) is not None:
                # App user is test name from call stack if inside a test
                self.app_user = test_name_from_call_stack
            else:
                # Use the username reported by OS if not testing
                os_user_id = getuser()
                self.app_user = os_user_id

    def cleanup_before(self) -> bool:
        """Cleanup deployment data (except logs) before each run if true."""
        if self.app_env in (AppEnv.PROD, AppEnv.STAGING):
            return False
        elif self.app_env in (AppEnv.DEV, AppEnv.TEMP):
            return True
        else:
            raise ErrorUtil.enum_value_error(self.app_env, AppEnv)

    def cleanup_after(self) -> bool:
        """Cleanup deployment data (except logs) after each run if true."""
        if self.app_env in (AppEnv.PROD, AppEnv.STAGING, AppEnv.DEV):
            return False
        elif self.app_env == AppEnv.TEMP:
            return True
        else:
            raise ErrorUtil.enum_value_error(self.app_env, AppEnv)
