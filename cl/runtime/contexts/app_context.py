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
from cl.runtime.contexts.context import Context
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.app_env import AppEnv
from cl.runtime.settings.app_settings import AppSettings


@dataclass(slots=True, kw_only=True)
class AppContext(Context):
    """Context for the naming and location of the app data."""

    env: AppEnv = required()
    """Determines the default settings for multiuser access and data retention."""

    name: str = required()
    """Identifies the application or test."""

    user: str = required()
    """Identifies the application or test user."""

    user_scoped: bool = required()  # TODO: Refactor and make the names more clear
    """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""

    @classmethod
    def get_base_type(cls) -> type:
        return AppContext

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Default values are based on settings (which may still be None) if not specified in the context
        app_settings = AppSettings.instance()
        self.env = self.env if self.env is not None else app_settings.app_env
        self.name = self.name if self.name is not None else app_settings.app_name
        self.user = self.user if self.user is not None else app_settings.app_user
        self.user_scoped = self.user_scoped if self.user_scoped is not None else app_settings.app_user_scoped

    @classmethod
    def get_env(cls) -> AppEnv:
        """Determines the default settings for multiuser access and data retention."""
        env = context.env if (context := cls.current_or_none()) is not None else AppSettings.instance().app_env
        if env is not None:
            return env
        else:
            # Default to DEV if not specified
            return AppEnv.DEV

    @classmethod
    def get_name(cls) -> str:
        """Identifies the application or test."""
        name = context.name if (context := cls.current_or_none()) is not None else AppSettings.instance().app_name
        if name is not None:
            return name
        else:
            # Default to Runtime if not specified
            return "Runtime"

    @classmethod
    def get_user(cls) -> str:
        """Identifies the application or test user."""
        user = context.user if (context := cls.current_or_none()) is not None else AppSettings.instance().app_user
        if user is not None:
            return user
        else:
            # Default to OS user if not specified
            return getuser()

    @classmethod
    def is_user_scoped(cls) -> bool:
        """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""
        user_scoped = (
            context.user_scoped
            if (context := cls.current_or_none()) is not None
            else AppSettings.instance().app_user_scoped
        )
        if user_scoped is not None:
            return user_scoped
        else:
            # Default user-scoped setting is based on env
            if (env := cls.get_env()) in (AppEnv.PROD, AppEnv.STAGING):
                # Data is shared between users by default for PROD and STAGING environments
                return True
            elif env in (AppEnv.DEV, AppEnv.TEMP):
                # Data is specific to each user by default for DEV and TEMP environments
                return False
            else:
                raise ErrorUtil.enum_value_error(env, AppEnv)

    @classmethod
    def is_cleanup_before(cls) -> bool:
        """Cleanup deployment data (except logs) before each run if true."""
        if (env := cls.get_env()) in (AppEnv.PROD, AppEnv.STAGING):
            return False
        elif env in (AppEnv.DEV, AppEnv.TEMP):
            return True
        else:
            raise ErrorUtil.enum_value_error(env, AppEnv)

    @classmethod
    def is_cleanup_after(cls) -> bool:
        """Cleanup deployment data (except logs) after each run if true."""
        if (env := cls.get_env()) in (AppEnv.PROD, AppEnv.STAGING, AppEnv.DEV):
            return False
        elif env == AppEnv.TEMP:
            return True
        else:
            raise ErrorUtil.enum_value_error(env, AppEnv)
