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

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.serializers.slots_util import SlotsUtil


class StubSlottedRecordKey(KeyMixin):
    """Stub record base class not using any dataclass framework."""

    __slots__ = SlotsUtil.merge_slots(DataMixin, "record_id")

    record_id: str
    """Unique identifier."""

    def __init__(self, record_id: str = "abc") -> None:
        """Initialize instance attributes."""
        super().__init__()
        self.record_id = record_id

    @classmethod
    def get_key_type(cls) -> type:
        return StubSlottedRecordKey
