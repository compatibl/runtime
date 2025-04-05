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
from typing import Any, Tuple, Dict, Callable
from typing import Iterable
from typing import List
from typing import Type
from typing import TypeVar

from memoization import cached

from cl.runtime import TypeImport
from cl.runtime.records.protocols import RecordProtocol, is_key_or_record, is_abstract
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil

T = TypeVar("T")

def is_non_abstract_key_or_record(class_: Type) -> bool:
    """Check if the class is a non-abstract record."""
    return is_key_or_record(class_) and not is_abstract(class_) and not class_.__name__.endswith("Mixin")

def is_non_mixin_key_or_record(class_: Type) -> bool:
    """Check if the class is a non-abstract record."""
    return is_key_or_record(class_) and not class_.__name__.endswith("Mixin")

class RecordUtil:
    """Utilities for working with records."""

    @classmethod
    @cached
    def child_records_of(cls, class_: Type) -> Tuple[Type, ...]:
        """Return a tuple of subclasses (inclusive of self) that are keys or records, excluding abstract and mixins."""
        if not is_key_or_record(class_):
            raise RuntimeError(
                f"Expected key or record, got {TypeUtil.name(class_)}\n"
                f"in '{cls.__name__}.child_records_of' method.")
        return TypeImport.subclasses_of(class_, predicate=is_non_abstract_key_or_record)

    @classmethod
    @cached
    def parent_records_of(cls, class_: Type) -> Tuple[Type, ...]:
        """Return a tuple of superclasses (inclusive of self) that are keys or records, excluding mixins."""
        if not is_key_or_record(class_):
            raise RuntimeError(
                f"Expected key or record, got {TypeUtil.name(class_)}\n"
                f"in '{cls.__name__}.parent_records_of' method.")
        return TypeImport.superclasses_of(class_, predicate=is_non_abstract_key_or_record)

    @classmethod
    def records_sharing_key_with(cls, class_: Type) -> Tuple[Type, ...]:
        """Return a tuple of classes sharing key with self (inclusive of self) that match the predicate, not cached."""
        if not is_key_or_record(class_):
            raise RuntimeError(
                f"Expected key or record, got {TypeUtil.name(class_)}\n"
                f"in '{cls.__name__}.child_records_of' method.")
        return TypeImport.records_sharing_key_with(class_, predicate=is_non_abstract_key_or_record)

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
