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
from getpass import getuser
from cl.runtime.contexts.env_util import EnvUtil
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.for_dataclasses.extensions import optional, required
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.settings.app_env import AppEnv
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class AppSettings(Settings):
    """Settings for the naming and location of the app data."""

    env: AppEnv = required()
    """Determines the default settings for multiuser access and data retention."""

    name: str = required()
    """Identifies the application or test."""

    user: str = required()
    """Identifies the application or test user."""

    user_scoped: bool = required()
    """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""

    _clear_before: bool = required(init=False)
    """Clear deployment data (except logs) before each run if true."""

    _clear_after: bool = required(init=False)
    """Clear deployment data (except logs) after each run if true."""

    _deployment_name: str = required(init=False)
    """Combines the app env, the app name and (for user-scoped deployments) user into a unique deployment name."""

    _deployment_dir: str = required(init=False)
    """Root directory for the files associated with the current deployment."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Override the default settings inside a test, this permits running testing on deployed apps
        if EnvUtil.is_inside_test():
            # Set the environment to TEST and the user to the test module name
            self.env = AppEnv.TEMP
            self.name = EnvUtil.get_env_name()
        else:
            # Set default values for env, name and user if not provided via Dynaconf
            if self.env is None:
                self.env = AppEnv.DEV
            if self.name is None:
                self.name = "Runtime"

        # Get the user from the running OS process if not provided via Dynaconf
        if self.user is None:
            self.user = getuser()

        # Default user-scoped setting
        if self.user_scoped is None:
            if self.env in (AppEnv.PROD, AppEnv.UAT):
                # Data is shared between users by default for PROD and UAT environments
                self.user_scoped = True
            elif self.env in (AppEnv.DEV, AppEnv.TEMP):
                # Data is specific to each user by default for DEV and TEMP environments
                self.user_scoped = False
            else:
                raise ErrorUtil.enum_value_error(self.env, AppEnv)

        # Set default values for clear_before and clear_after
        if self.env in (AppEnv.PROD, AppEnv.UAT):
            self._clear_before = False
            self._clear_after = False
        elif self.env == AppEnv.DEV:
            self._clear_before = True
            self._clear_after = False
        elif self.env == AppEnv.TEMP:
            self._clear_before = True
            self._clear_after = True
        else:
            raise ErrorUtil.enum_value_error(self.env, AppEnv)

        # Set deployment name and directory
        # TODO: Add checks to ensure the name does not have invalid characters
        env_name = EnumSerializers.DEFAULT.serialize(self.env)
        if self.user_scoped:
            self._deployment_name = f"{env_name};{self.name};{self.user}"
        else:
            self._deployment_name = f"{env_name};{self.name}"

        # Override deployment directory if inside a test
        if EnvUtil.is_inside_test():
            # Unique subdirectory for each test function or method under the test directory
            self._deployment_dir = EnvUtil.get_env_dir()
        else:
            # Unique subdirectory for each deployment under the project root
            project_root = ProjectSettings.get_project_root()
            self._deployment_dir = os.path.join(project_root, "deployments", self._deployment_name)

        # Create deployment directory if it does not exist
        if not os.path.exists(self._deployment_dir):
            os.makedirs(self._deployment_dir)

    @classmethod
    def is_user_scoped(cls) -> bool:
        """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""
        return bool(cls.instance().user_scoped)

    @classmethod
    def clear_before(cls) -> bool:
        """Clear deployment data (except logs) before each run if true."""
        return bool(cls.instance()._clear_before)

    @classmethod
    def clear_after(cls) -> bool:
        """Clear deployment data (except logs) after each run if true."""
        return bool(cls.instance()._clear_after)

    @classmethod
    def get_deployment_name(cls) -> str:
        """Combines the app env, the app name and (for user-scoped deployments) user into a unique deployment name."""
        return cls.instance()._deployment_name

    @classmethod
    def get_deployment_dir(cls) -> str:
        """Root directory for the files associated with the current deployment."""
        return cls.instance()._deployment_dir

    @classmethod
    def get_prefix(cls) -> str:
        return "runtime_app"
