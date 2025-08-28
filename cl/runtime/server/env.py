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

from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.server.env_key import EnvKey
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.env_settings import EnvSettings


@dataclass(slots=True, kw_only=True)
class Env(EnvKey, RecordMixin):
    """Application environment parameters."""

    env_kind: EnvKind = required()
    """Determines the default settings for multiuser access and data retention."""

    name: str | None = None
    """Identifies the application or test."""

    user: str = required()
    """Identifies the application or test user."""

    def get_key(self) -> EnvKey:
        return EnvKey(env_id=self.env_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if (active := active_or_none(Env)) is not None:
            # Default to the active environment if present, allow to override
            self.env_id = self.env_id if self.env_id is not None else active.env_id
            self.env_kind = self.env_kind if self.env_kind is not None else active.env_kind
            self.name = self.name if self.name is not None else active.name
            self.user = self.user if self.user is not None else active.user
        else:
            # Use test root process detection only if env_kind is None to prevent override in worker processes
            if QaUtil.is_test_root_process():
                if self.env_kind is None:
                    self.env_kind = EnvKind.TEST
                elif self.env_kind != EnvKind.TEST:
                    raise RuntimeError(f"Field env_kind must be set to TEST inside a test.")

            if self.env_kind == EnvKind.TEST:
                # Inside a test, override settings for these fields if not yet set and configure them for a test
                self.env_id = self.env_id if self.env_id is not None else QaUtil.get_test_name_from_call_stack()
                # Use settings for other fields if not yet set
                settings = EnvSettings.instance()
                # self.name = self.name if self.name is not None else settings.name
                self.user = self.user if self.user is not None else settings.env_user
            else:
                # Otherwise use settings for all fields that are not yet set
                settings = EnvSettings.instance()
                self.env_id = self.env_id if self.env_id is not None else settings.env_id
                self.env_kind = self.env_kind if self.env_kind is not None else settings.env_kind
                # self.name = self.name if self.name is not None else settings.name
                self.user = self.user if self.user is not None else settings.env_user

        # Error if env_kind is not TEST but we are inside a root test process
        if self.env_kind != EnvKind.TEST and QaUtil.is_test_root_process():
            test_name = QaUtil.get_test_name_from_call_stack()
            raise RuntimeError(f"Env.is_test must not be True inside a test root process.\nTest name: {test_name}.")

    def is_test(self) -> bool:  # TODO: DEPRECATED, USE ENV TO SET PARAMS INSTEAD
        """True for the root process or worker processes of a test, False when not a test."""
        return self.env_kind == EnvKind.TEST

    @classmethod
    def get_env(cls) -> EnvKind:
        """Determines the default settings for multiuser access and data retention."""
        env = context.env_kind if (context := cls.current_or_none()) is not None else EnvSettings.instance().env_kind
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
