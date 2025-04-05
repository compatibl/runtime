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

from inspect import isabstract
from typing import Any
from typing import Iterable
from typing import List
from typing import Type
from typing import TypeVar
from cl.runtime.records.protocols import RecordProtocol, is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil

T = TypeVar("T")


class RecordUtil:
    """Utilities for working with records."""

    @classmethod
    def get_non_abstract_descendants(cls, record_type: Type) -> List[Type]:
        """Find non-abstract descendants of 'record_type' to all levels and return their types."""
        # TODO: Add caching, convert to tuple
        subclasses = record_type.__subclasses__()
        result = []
        for subclass in subclasses:
            # Recursively check subclasses
            result.extend(cls.get_non_abstract_descendants(subclass))
            # If the subclass is not abstract, add it to the list
            if not isabstract(subclass):
                result.append(subclass)
        return result
    
    @classmethod
    def get_non_abstract_ancestors(cls, record_type: Type) -> List[Type]:
        """
        Return non-abstract record ancestors in the order from derived to base, starting from self and ending with key.
        """
        # TODO: Add caching, convert to tuple
        # Get the list of classes in MRO that are keys or records and are not mixins or abstract
        result = [
            x
            for x in record_type.mro()
            if is_key_or_record(x) and not isabstract(x) and not x.__name__.endswith("Mixin")
        ]

        # Make sure there is only one such class in the inheritance chain
        if len(result) == 0:
            raise RuntimeError(f"Class {TypeUtil.name(record_type)} is not a record or key.")
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
