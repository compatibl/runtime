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
from cl.runtime.records.query_mixin import QueryMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic


@dataclass(slots=True, kw_only=True)
class StubDataclassPolymorphicQuery(QueryMixin):
    """Query for the stub record with a polymorphic key."""

    table_field: str = required()
    """Specifies the table where this record is stored."""

    key_field: str | None = None
    """Unique within this table where this record is stored."""

    record_field: str | None = None
    """Stub field of the record."""

    @classmethod
    def get_target_type(cls) -> type:
        return StubDataclassPolymorphic

    def get_partition(self) -> str | None:
        return self.table_field

