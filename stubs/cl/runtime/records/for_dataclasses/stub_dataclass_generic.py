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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg import StubDataclassGenericArg
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_key import StubDataclassGenericKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_key import TKeyArg

TRecordArg = TypeVar("TRecordArg", bound=StubDataclassGenericArg)


@dataclass(slots=True, kw_only=True)
class StubDataclassGeneric(
    Generic[TKeyArg, TRecordArg],
    StubDataclassGenericKey[TKeyArg],
    RecordMixin[StubDataclassGenericKey[TKeyArg]],
):
    """Stub dataclass-based generic record."""

    record_field: TRecordArg | None = None
    """Optional field with generic type."""

    def get_key(self) -> StubDataclassGenericKey[TKeyArg]:
        return StubDataclassGenericKey(key_field=StubDataclassKey()).build()
