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

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.views.view import View
from cl.runtime.views.view_key import ViewKey
from cl.runtime.views.view_key_query import ViewKeyQuery


class ViewPersistenceUtil:
    """Util class with methods for persistent views."""

    @classmethod
    def load_view_or_none(cls, view_for: KeyMixin, view_name: str) -> View | None:
        """Load persisted view or return None if it does not exist."""
        persisted_view = active(DataSource).load_one_or_none(
            key_or_record=ViewKey(view_for=view_for, view_name=view_name).build()
        )
        return persisted_view

    @classmethod
    def load_all_views_for_record(cls, record: KeyMixin) -> list[View]:
        """Load all persisted views for a record."""
        query = ViewKeyQuery(view_for=record).build()
        persisted_views = active(DataSource).load_by_query(
            query=query,
        )
        return list(persisted_views)

    @classmethod
    def get_panel_kind_from_view(cls, view: View) -> str | None:
        """Get type of the view."""
        if view.view_name == "view_self":
            return "Primary"
        return None
