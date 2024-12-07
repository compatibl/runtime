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
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_abstract_record import StubDataclassAbstractRecord  # type: ignore
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_key import StubDataclassFinalKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_record import StubDataclassFinalRecord


@dataclass(slots=True, kw_only=True)
class StubDataclassNestedFinalRecord(StubDataclassRecord):
    """Some of the fields are in base record."""

    final_key:  StubDataclassFinalKey = StubDataclassFinalKey()
    """Final key field."""

    final_record: StubDataclassFinalRecord = StubDataclassFinalRecord()
    """Final record field."""





