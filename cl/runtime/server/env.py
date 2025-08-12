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

from cl.runtime import RecordMixin
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.server.env_key import EnvKey
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.env_settings import EnvSettings


@dataclass(slots=True, kw_only=True)
class Env(EnvKey, RecordMixin):
    """Application environment parameters."""

    testing: bool | None = None
    """True for the root process or worker processes of a test, False when not a test."""

    env: EnvKind = required()
    """Determines the default settings for multiuser access and data retention."""

    name: str = required()
    """Identifies the application or test."""

    user: str = required()
    """Identifies the application or test user."""

    user_scoped: bool = required()  # TODO: Refactor and make the names more clear
    """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""

    def get_key(self) -> EnvKey:
        return EnvKey(env_id=self.env_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.testing is None:
            # Can be set here based on detecting the root process of a test because ContextSnapshot
            # will initialize this field for the worker processes launched by the test
            self.testing = QaUtil.is_test_root_process()

        # Default values are based on settings (which may still be None) if not specified in the context
        env_settings = EnvSettings.instance()
        self.env_id = self.env_id if self.env_id is not None else env_settings.env_id
        self.env = self.env if self.env is not None else env_settings.env_kind
        self.name = self.name if self.name is not None else env_settings.env_id
        self.user = self.user if self.user is not None else env_settings.env_user
        self.user_scoped = self.user_scoped if self.user_scoped is not None else env_settings.env_shared

    @classmethod
    def get_env(cls) -> EnvKind:
        """Determines the default settings for multiuser access and data retention."""
        env = context.env if (context := cls.current_or_none()) is not None else EnvSettings.instance().env_kind
        if env is not None:
            return env
        else:
            # Default to DEV if not specified
            return EnvKind.DEV

    @classmethod
    def get_name(cls) -> str:
        """Identifies the application or test."""
        name = context.name if (context := cls.current_or_none()) is not None else EnvSettings.instance().env_id
        if name is not None:
            return name
        else:
            # Default to Runtime if not specified
            return "Runtime"

    @classmethod
    def get_user(cls) -> str:
        """Identifies the application or test user."""
        user = context.user if (context := cls.current_or_none()) is not None else EnvSettings.instance().env_user
        if user is not None:
            return user
        else:
            # Default to OS user if not specified
            return getuser()

    @classmethod
    def is_user_scoped(cls) -> bool:
        """Deployment data is fully isolated for each user if true and shared if false (user must be set either way)."""
        user_scoped = (
            context.user_scoped if (context := cls.current_or_none()) is not None else EnvSettings.instance().env_shared
        )
        if user_scoped is not None:
            return user_scoped
        else:
            # Default user-scoped setting is based on env
            if (env := cls.get_env()) in (EnvKind.PROD, EnvKind.STAGING):
                # Data is shared between users by default for PROD and STAGING environments
                return True
            elif env in (EnvKind.DEV, EnvKind.TEMP):
                # Data is specific to each user by default for DEV and TEMP environments
                return False
            else:
                raise ErrorUtil.enum_value_error(env, EnvKind)

    @classmethod
    def is_cleanup_before(cls) -> bool:
        """Cleanup deployment data (except logs) before each run if true."""
        if (env := cls.get_env()) in (EnvKind.PROD, EnvKind.STAGING):
            return False
        elif env in (EnvKind.DEV, EnvKind.TEMP):
            return True
        else:
            raise ErrorUtil.enum_value_error(env, EnvKind)

    @classmethod
    def is_cleanup_after(cls) -> bool:
        """Cleanup deployment data (except logs) after each run if true."""
        if (env := cls.get_env()) in (EnvKind.PROD, EnvKind.STAGING, EnvKind.DEV):
            return False
        elif env == EnvKind.TEMP:
            return True
        else:
            raise ErrorUtil.enum_value_error(env, EnvKind)
