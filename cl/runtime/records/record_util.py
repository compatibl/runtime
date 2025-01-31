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

import inspect
from typing import Any, TypeVar
from typing import Iterable
from typing import List
from typing import Type
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_record

T = TypeVar("T")


class RecordUtil:
    """Utilities for working with records."""

    @classmethod
    def is_abstract(cls, record_type: Type) -> bool:
        """Return True if 'record_type' is abstract."""
        return bool(inspect.isabstract(record_type))

    @classmethod
    def get_non_abstract_descendants(cls, record_type: Type) -> List[Type]:
        """Find non-abstract descendants of 'record_type' to all levels and return the list of ClassName."""
        subclasses = record_type.__subclasses__()
        result = []
        for subclass in subclasses:
            # Recursively check subclasses
            result.extend(cls.get_non_abstract_descendants(subclass))
            # If the subclass is not abstract, add it to the list
            if not inspect.isabstract(subclass):
                result.append(subclass)
        return result

    @classmethod
    def sort_records_by_key(cls, records: Iterable[RecordProtocol]) -> List[RecordProtocol]:
        """Sort records by string key fields."""

        # TODO (Roman): Check string key fields in nested keys
        sort_records: Any = []
        for record in records:
            # TODO: Refactor to use a key serializer
            key_slots = record.get_key().__slots__ if is_record(record) else tuple()  # noqa
            str_key_values = [v for slot in key_slots if isinstance((v := getattr(record, slot)), str)]
            sort_key = ";".join(str_key_values)
            sort_records.append((sort_key, record))

        return [record for _, record in sorted(sort_records, key=lambda x: x[0])]
