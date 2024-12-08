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
from typing import TYPE_CHECKING
from typing import Any
from typing import Type
from cl.runtime.records.empty_mixin import EmptyMixin
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_abstract_record import (
    StubDataclassAbstractRecord,  # type: ignore
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_key import StubDataclassFinalKey

KEY_TYPE = StubDataclassFinalKey if TYPE_CHECKING else EmptyMixin


@dataclass(slots=True, kw_only=True)
class StubDataclassFinalRecord(StubDataclassAbstractRecord, RecordMixin[StubDataclassFinalKey], KEY_TYPE):
    """Some of the fields are in base record."""

    final_field: str = "abc"
    """Field in base record."""

    @classmethod
    def get_key_type(cls) -> Type:
        return StubDataclassFinalKey

    def get_key(self) -> StubDataclassFinalKey:
        return StubDataclassFinalKey(id=self.id)
