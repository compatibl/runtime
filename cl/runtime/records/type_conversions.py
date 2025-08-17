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

from typing import Sequence

from cl.runtime.records.protocols import KeyProtocol, RecordProtocol
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename


class TypeConversions:
    """Perform type conversions."""

    @classmethod
    def to_key_sequence(cls, keys: KeyProtocol | Sequence[KeyProtocol]) -> Sequence[KeyProtocol]:
        """Convert input key to key sequence and pass through if already a key sequence, with validation."""
        if TypeCheck.guard_key_instance(keys, raise_on_fail=False):
            # Single key, convert to tuple
            return (keys,)
        elif TypeCheck.guard_key_sequence(keys, raise_on_fail=False):
            # Already a sequence of keys
            return keys
        else:
            raise RuntimeError(
                f"Parameter 'keys' of type {typename(keys)} is not a key or a sequence of keys\n"
                f"(iterable generator is not accepted)")

    @classmethod
    def to_record_sequence(cls, records: RecordProtocol | Sequence[RecordProtocol]) -> Sequence[RecordProtocol]:
        """Convert input record to record sequence and pass through if already a record sequence, with validation."""
        if TypeCheck.guard_record_instance(records, raise_on_fail=False):
            # Single record, convert to tuple
            return (records,)
        elif TypeCheck.guard_record_sequence(records, raise_on_fail=False):
            # Already a sequence of records
            return records
        else:
            raise RuntimeError(
                f"Parameter 'records' of type {typename(records)} is not a record or a sequence of records\n"
                f"(iterable generator is not accepted)")
