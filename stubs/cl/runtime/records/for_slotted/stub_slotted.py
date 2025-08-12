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

from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.serializers.slots_util import SlotsUtil
from stubs.cl.runtime.records.for_slotted.stub_slotted_key import StubSlottedKey


class StubSlotted(StubSlottedKey, RecordMixin):
    """Stub record base class not using any dataclass framework."""

    __slots__ = ("record_field",)

    record_field: str
    """Field of the record object."""

    def __init__(self, key_field: str = "abc", record_field: str = "def") -> None:
        """Initialize instance attributes."""
        super().__init__(key_field)
        self.record_field = record_field

    def get_key(self) -> StubSlottedKey:
        return StubSlottedKey(key_field=self.key_field).build()
