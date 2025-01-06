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
from dataclasses import field
from typing import Any
from typing import List
from cl.runtime import RecordMixin
from cl.runtime.records.record_mixin import TKey
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_any_fields_key import StubDataclassAnyFieldsKey


@dataclass(slots=True, kw_only=True)
class StubDataclassAnyFields(StubDataclassAnyFieldsKey, RecordMixin[StubDataclassAnyFieldsKey]):

    any_str: Any = "any_str"
    """Any str value."""

    any_key: Any = StubDataclassRecordKey()
    """Any key value."""

    any_record: Any = StubDataclassRecord()
    """Any record value."""

    list_of_any: List[Any] = field(
        default_factory=lambda: ["any_str", 1, 1.1, StubDataclassRecordKey(), StubDataclassRecord()]
    )
    """List of any values."""

    def get_key(self) -> TKey:
        return StubDataclassAnyFieldsKey(id=self.id)
