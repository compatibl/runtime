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
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.query_mixin import QueryMixin
from cl.runtime.records.table_binding import TableBinding
from cl.runtime.records.conditions import Condition

@dataclass(slots=True, kw_only=True)
class TableBindingQuery(QueryMixin):
    """Query for TableBinding."""

    key_type: str | Condition[str] | None = None
    """Key type for the records in this table."""

    def get_target_type(self) -> type[KeyMixin]:
        return TableBinding
