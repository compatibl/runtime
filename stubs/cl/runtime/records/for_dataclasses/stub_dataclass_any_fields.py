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
from typing import Any
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_any_fields_key import StubDataclassAnyFieldsKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


@dataclass(slots=True, kw_only=True)
class StubDataclassAnyFields(StubDataclassAnyFieldsKey, RecordMixin):

    any_str: Any = "any_str"
    """Any str value."""

    any_key: Any = optional(default_factory=lambda: StubDataclassKey())
    """Any key value."""

    any_record: Any = optional(default_factory=lambda: StubDataclass())
    """Any record value."""

    list_of_any: list[Any] = optional(default_factory=lambda: ["any_str", 1, 1.1, StubDataclassKey(), StubDataclass()])
    """List of any values."""

    def get_key(self) -> StubDataclassAnyFieldsKey:
        return StubDataclassAnyFieldsKey(id=self.id).build()
