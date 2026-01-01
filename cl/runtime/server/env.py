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
from cl.runtime.contexts.context_manager import active_or_none
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

    env_user: str = required()
    """Identifies the application or test user (defaults to the OS user)."""

    env_tenant: str = required()
    """Unique tenant identifier, tenants are isolated when sharing the same DB (defaults to env_user)."""

    env_dir: str = required()
    """
    Defaults to the value in settings if not specified. The following variables can be used inside braces:

    - env_id
    - env_kind
    - env_user
    - env_tenant
    """

    def get_key(self) -> EnvKey:
        return EnvKey(env_id=self.env_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if (active := active_or_none(Env)) is not None:
            # Default to the active environment if present, allow to override
            self.env_id = self.env_id if self.env_id is not None else active.env_id
            self.env_kind = self.env_kind if self.env_kind is not None else active.env_kind
            self.env_user = self.env_user if self.env_user is not None else active.env_user
            self.env_tenant = self.env_tenant if self.env_tenant is not None else active.env_tenant
            self.env_dir = self.env_dir if self.env_dir is not None else active.env_dir
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
                self.env_dir = self.env_dir if self.env_dir is not None else QaUtil.get_test_dir_from_call_stack()
                # Use settings for other fields if not yet set
                settings = EnvSettings.instance()
                self.env_user = self.env_user if self.env_user is not None else settings.env_user
                self.env_tenant = self.env_tenant if self.env_tenant is not None else settings.env_tenant
            else:
                # Otherwise use settings for all fields that are not yet set
                settings = EnvSettings.instance()
                self.env_id = self.env_id if self.env_id is not None else settings.env_id
                self.env_kind = self.env_kind if self.env_kind is not None else settings.env_kind
                self.env_user = self.env_user if self.env_user is not None else settings.env_user
                self.env_tenant = self.env_tenant if self.env_tenant is not None else settings.env_tenant
                self.env_dir = self.env_dir if self.env_dir is not None else settings.env_dir

    def is_test(self) -> bool:  # TODO: DEPRECATED, USE ENV TO SET PARAMS INSTEAD
        """True for the root process or worker processes of a test, False when not a test."""
        return self.env_kind == EnvKind.TEST
