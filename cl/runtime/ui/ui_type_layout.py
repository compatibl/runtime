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
from typing import final
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.ui.layout_element_base import LayoutElementBase
from cl.runtime.ui.ui_type_layout_key import UiTypeLayoutKey


@final
@dataclass(slots=True, kw_only=True)
class UiTypeLayout(UiTypeLayoutKey, RecordMixin):
    """Represents of the type's layout."""

    layout: list[LayoutElementBase] | None = None
    """Layout elements."""

    maximized_tab_id: str | None = None
    """Name of the active maximized tab. None if no maximized panels."""

    def get_key(self) -> UiTypeLayoutKey:
        return UiTypeLayoutKey(type_=self.type_, user=self.user)
