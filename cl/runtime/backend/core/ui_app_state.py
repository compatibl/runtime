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
from typing import Dict
from typing import List
from cl.runtime.backend.core.tab_info import TabInfo
from cl.runtime.backend.core.ui_app_state_key import UiAppStateKey
from cl.runtime.backend.core.user_key import UserKey
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class UiAppState(UiAppStateKey, RecordMixin[UiAppStateKey]):
    """UiAppState."""

    opened_tabs: List[TabInfo] | None = None
    """Information about opened tabs."""

    active_tab_index: int | None = None
    """Index of active opened tab."""

    backend_version: str | None = None
    """DEPRECATED. Use versions instead."""

    versions: Dict[str, str] | None = None
    """Component versions."""

    application_name: str | None = None
    """Application name."""

    read_only: bool | None = None
    """Flag indicating that UI is read-only."""

    application_theme: str | None = None
    """Application theme (dark, light, etc.)."""

    user_secret_identifiers: List[str] | None = None
    """
    Suggested key names in My Keys section of the head and shoulders dialog.

    Notes:
        - This is a list of suggestions, no restriction on entering secrets with other names
        - The secret names should be in snake_case, for example ["openai_api_key", "anthropic_api_key"] 
    """

    def get_key(self) -> UiAppStateKey:
        return UiAppStateKey(user=self.user).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.application_theme not in (application_themes := [None, "System", "Dark", "Light", "Blue"]):
            raise RuntimeError(
                f"Field UiAppState.application_theme has the value of {self.application_theme}\n"
                f"Permitted values are {', '.join(application_themes[1:])}")

    @classmethod
    def get_current_user_app_theme(cls) -> str | None:
        """Get current user app theme."""

        default_app_state_key = UiAppStateKey(
            user=UserKey(username="root")
        ).build()  # TODO: Review the use of root default

        default_app_state = DbContext.load_one_or_none(UiAppState, default_app_state_key)
        if default_app_state is not None and default_app_state.application_theme is not None:
            return default_app_state.application_theme

        # Default to System if not previously selected by the user
        return "System"
