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
from cl.runtime.log.ui_clear_logs_marker_key import UiClearLogsMarkerKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class UiClearLogsMarker(UiClearLogsMarkerKey, RecordMixin):
    """Record to mark the point when the logs were cleared in UI."""

    def get_key(self) -> KeyMixin:
        return UiClearLogsMarkerKey(clear_logs_timestamp=self.clear_logs_timestamp).build()

    def __init(self):
        if self.clear_logs_timestamp is None:
            self.clear_logs_timestamp = Timestamp.create()
