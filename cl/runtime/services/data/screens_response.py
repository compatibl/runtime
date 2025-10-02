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

from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.services.data.filter_screen_item import FilterScreenItem
from cl.runtime.services.data.table_screen_item import TableScreenItem
from cl.runtime.services.data.type_screen_item import TypeScreenItem


class ScreensResponse(PydanticMixin):
    """Class for screens data."""

    tables: list[TableScreenItem]
    """List of Tables that can be selected."""

    types: list[TypeScreenItem]
    """List of Types that can be selected."""

    filters: list[FilterScreenItem]
    """List of Filters that can be selected."""
