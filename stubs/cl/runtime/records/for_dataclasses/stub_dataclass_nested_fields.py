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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_data import StubDataclassDerivedData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_from_derived_data import (
    StubDataclassDerivedFromDerivedData,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecordKey


@dataclass(slots=True, kw_only=True)
class StubDataclassNestedFields(StubDataclassRecord):
    """Stub derived class."""

    base_field: StubDataclassData = required(default_factory=lambda: StubDataclassData())
    """Stub field."""

    derived_field: StubDataclassDerivedData = required(default_factory=lambda: StubDataclassDerivedData())
    """Stub field."""

    derived_from_derived_field: StubDataclassDerivedFromDerivedData = required(
        default_factory=lambda: StubDataclassDerivedFromDerivedData()
    )
    """Stub field."""

    polymorphic_field: StubDataclassData = required(default_factory=lambda: StubDataclassDerivedData())
    """Declared StubDataclassData but provided an instance of StubDataclassDerivedData."""

    polymorphic_derived_field: StubDataclassDerivedData = required(default_factory=lambda: StubDataclassDerivedFromDerivedData())
    """Declared StubDataclassDerivedData but provided an instance of StubDataclassDerivedFromDerivedData."""

    key_field: StubDataclassRecordKey = required(default_factory=lambda: StubDataclassRecordKey(id="uvw"))
    """Stub field."""

    record_as_key_field: StubDataclassRecordKey = required(default_factory=lambda: StubDataclassRecord())
    """Stub field with key type initialized to record type instance."""
