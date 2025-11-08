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
from typing_extensions import final
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.ui.column_state import ColumnState
from cl.runtime.ui.layout_element import LayoutElement
from cl.runtime.ui.ui_type_state_key import UiTypeStateKey


@final
@dataclass(slots=True, kw_only=True)
class UiTypeState(UiTypeStateKey, RecordMixin):
    """Defines ui settings for a type."""

    read_only: bool | None = None
    """Specifies if records of this type are readonly."""

    hide_editor: bool | None = None
    """Specifies if Editor tab should be hidden."""

    use_cache: bool | None = None
    """
    If set and TRUE data will be cached until tab is opened. This means that the next time the tab is
    activated, the main grid data request will not be submitted, it will be taken from the browser cache.
    """

    pinned_handlers: list[str] | None = None
    """List of names of the handlers pinned for the type"""

    layout: list[LayoutElement] | None = None
    """Layout elements."""

    columns_state: list[ColumnState] | None = None
    """List of column specific state attributes."""

    main_grid_cell_height: int | None = None
    """
    The number of lines to be displayed in the main grid within a cell refers to the maximum
    number of text lines that can be shown in each cell.
    """

    maximized_tab_id: str | None = None
    """Obsolete. Name of the active maximized tab. None if no maximized panels."""

    page_index: int | None = None
    """The zero-based index of the page to fetch. For example, 0 returns the first page, 1 the second, etc. 0 is the default value."""

    page_size: int | None = None
    """The number of records to return per page in the paginated result set. 1000 is the default value."""

    user_guide_content: str | None = None
    """
    Represents the content of the user guide.
    """

    user_guide_format: str | None = None
    """
    Specifies the format of the user guide (e.g., 'Markdown', 'HTML').
    """

    user_guide_completed: bool | None = None
    """
    Indicates whether the user guide has been completed.
    """

    def get_key(self) -> UiTypeStateKey:
        return UiTypeStateKey(type_=self.type_, user=self.user).build()
