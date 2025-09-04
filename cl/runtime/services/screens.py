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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.services.filter_screen_item import FilterScreenItem
from cl.runtime.services.table_screen_item import TableScreenItem
from cl.runtime.services.type_screen_item import TypeScreenItem


@dataclass(slots=True, kw_only=True)
class Screens(DataclassMixin):
    """Class for screens data."""

    tables: list[TableScreenItem] = required()
    """List of Tables that can be selected."""

    types: list[TypeScreenItem] = required()
    """List of Types that can be selected."""

    filters: list[FilterScreenItem] = required()
    """List of Filters that can be selected."""
