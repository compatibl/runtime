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

from typing import Any
from typing import Iterable
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.protocols import is_record


class RecordUtil:
    """Utilities for working with records."""

    @classmethod
    def sort_records_by_key(cls, records: Iterable[RecordMixin]) -> tuple[RecordMixin]:
        """Sort records by string key fields."""

        # TODO (Roman): Check string key fields in nested keys
        sort_records: Any = []
        for record in records:
            # TODO: Refactor to use a key serializer
            key_slots = record.get_key().get_field_names() if is_record(record) else tuple()  # noqa
            str_key_values = [v for slot in key_slots if isinstance((v := getattr(record, slot)), str)]
            sort_key = ";".join(str_key_values)
            sort_records.append((sort_key, record))

        return tuple(record for _, record in sorted(sort_records, key=lambda x: x[0]))
