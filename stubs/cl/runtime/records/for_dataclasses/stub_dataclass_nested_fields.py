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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_data import StubDataclassData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_data import StubDataclassDerivedData
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_double_derived_data import StubDataclassDoubleDerivedData


@dataclass(slots=True, kw_only=True)
class StubDataclassNestedFields(StubDataclass):
    """Stub derived class."""

    base_field: StubDataclassData = required(default_factory=lambda: StubDataclassData())
    """Stub field."""

    derived_field: StubDataclassDerivedData = required(default_factory=lambda: StubDataclassDerivedData())
    """Stub field."""

    double_derived_field: StubDataclassDoubleDerivedData = required(
        default_factory=lambda: StubDataclassDoubleDerivedData()
    )
    """Stub field."""

    polymorphic_field: StubDataclassData = required(default_factory=lambda: StubDataclassDerivedData())
    """Declared StubDataclassData but provided an instance of StubDataclassDerivedData."""

    polymorphic_derived_field: StubDataclassDerivedData = required(
        default_factory=lambda: StubDataclassDoubleDerivedData()
    )
    """Declared StubDataclassDerivedData but provided an instance of StubDataclassDoubleDerivedData."""

    key_field: StubDataclassKey = required(default_factory=lambda: StubDataclassKey(id="uvw"))
    """Stub field."""

    record_as_key_field: StubDataclassKey = required(default_factory=lambda: StubDataclass())
    """Stub field with key type initialized to record type instance."""
