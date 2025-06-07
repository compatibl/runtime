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
from typing import Generic
from typing import TypeVar
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_bound_generic_key import StubDataclassBoundGenericKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg import StubDataclassGenericArg

TRecordArg1 = TypeVar("TRecordArg1", bound=StubDataclassGenericArg)
TRecordArg2 = TypeVar("TRecordArg2", bound=StubDataclassGenericArg)

@dataclass(slots=True, kw_only=True)
class StubDataclassGeneric(Generic[TRecordArg1, TRecordArg2],
    StubDataclassBoundGenericKey,
    RecordMixin[StubDataclassBoundGenericKey],
):
    """Stub dataclass-based generic record."""

    record_field_1: TRecordArg1 | None = None
    """Optional field with generic type."""

    record_field_2: TRecordArg2 | None = None
    """Optional field with generic type."""

    def get_key(self) -> StubDataclassBoundGenericKey:
        return StubDataclassBoundGenericKey(key_field=self.key_field).build()
