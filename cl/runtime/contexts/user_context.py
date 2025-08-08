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
from typing import Dict
from cl.runtime.backend.core.user_key import UserKey
from cl.runtime.contexts.context_mixin import ContextMixin
from cl.runtime.contexts.process_context import ProcessContext
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class UserContext(ContextMixin, DataMixin):
    """User-specific settings and data."""

    user: UserKey = required()
    """Current user."""

    encrypted_secrets: Dict[str, str] | None = None
    """User secrets specified here take precedence over those defined via Dynaconf."""

    @classmethod
    def get_base_type(cls) -> type:
        return UserContext

    @classmethod
    def get_user(cls) -> UserKey:
        """Return the user specified in current UserContext, or user reported by OS outside the outermost 'with'."""
        if (user_context := UserContext.current_or_none()) is not None:
            # User for the current UserContext
            return user_context.user
        elif ProcessContext.is_testing():
            # Use process namespace as the user
            return UserKey(username=QaUtil.get_test_name_from_call_stack())
        else:
            # User reported by OS
            os_user_id = getuser()
            return UserKey(username=os_user_id)
