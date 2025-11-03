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
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.records.predicates import Predicate
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_type_presence_key import RecordTypePresenceKey


@dataclass(slots=True, kw_only=True)
class RecordTypePresenceQuery(DataclassMixin, QueryMixin):
    """Query for RecordTypePresence by the key_type field."""

    key_type: type | Predicate[type] | None = None
    """Use to query for record types stored in the table for this key type."""

    def get_target_type(self) -> type[KeyMixin]:
        return RecordTypePresenceKey
