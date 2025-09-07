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
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.record_type_presence_key import RecordTypePresenceKey
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typenameof


@dataclass(slots=True, kw_only=True)
class RecordTypePresence(RecordTypePresenceKey, RecordMixin):
    """Indicates that DB has a table for the specified record type."""

    key_type: type = required()
    """Use to query for record types stored in the table for this key type."""

    def get_key(self) -> RecordTypePresenceKey:
        return RecordTypePresenceKey(record_type=self.record_type).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if not is_record_type(self.record_type):
            raise RuntimeError(
                f"Field {typenameof(self)}.record_type={typename(self.record_type)} is not a record type."
            )
        if not is_key_type(self.key_type):
            raise RuntimeError(f"Field {typenameof(self)}.key_type={typename(self.key_type)} is not a key type.")
