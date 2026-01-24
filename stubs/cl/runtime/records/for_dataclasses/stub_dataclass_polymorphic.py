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
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_base_key import StubDataclassPolymorphicBaseKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey


@dataclass(slots=True, kw_only=True)
class StubDataclassPolymorphic(StubDataclassPolymorphicKey, RecordMixin):
    """Stub record class derived from StubDataclassPolymorphicKey."""

    record_field: str = "record_field"
    """The presence of this field indicates a record rather than key is stored."""

    base_key_field: StubDataclassPolymorphicBaseKey | None = None
    """The type of this field is not the record's key type but its base."""

    root_key_field: KeyMixin | None = optional(default_factory=StubDataclassKey)
    """The type of this field is not the record's key type but KeyMixin."""

    record_as_base_key_field: StubDataclassPolymorphicBaseKey | None = None
    """The type of this field is not the record's key type but its base, the value is a record."""

    record_as_root_key_field: KeyMixin | None = None
    """The type of this field is not the record's key type but KeyMixin, the value is a record."""

    def get_key(self) -> StubDataclassPolymorphicKey:
        return StubDataclassPolymorphicKey(id=self.id).build()
