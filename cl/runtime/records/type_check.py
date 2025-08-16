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
from typing import Sequence
from typing import TypeGuard
from memoization import cached
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename


class TypeCheck:
    """Performs runtime type checks and returns TypeGuard instance."""

    @classmethod
    @cached
    def is_key_type(cls, key_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a key type."""
        if isinstance(key_type, type) and is_key(key_type):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_type)} is not a key type.")
        else:
            return False

    @classmethod
    @cached
    def is_key_instance(cls, key: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a key instance."""
        if not isinstance(key, type) and is_key(key):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(key)} is not a key instance.")
        else:
            return False

    @classmethod
    @cached
    def is_key_instance_or_none(cls, key: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol | None]:
        """Check if the argument is a key instance or None."""
        if key is None or (not isinstance(key, type) and is_key(key)):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(key)} is not a key instance or None.")
        else:
            return False

    @classmethod
    def is_key_sequence(cls, keys: Any, *, raise_on_fail: bool = True) -> TypeGuard[Sequence[KeyProtocol]]:
        """Check if the argument is a key sequence (iterable generator is not accepted)."""
        if is_sequence(keys):
            return all(cls.is_key_instance(x, raise_on_fail=raise_on_fail) for x in keys)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def is_key_sequence_or_none(
        cls, keys: Any, *, raise_on_fail: bool = True
    ) -> TypeGuard[Sequence[KeyProtocol] | None] | None:
        """
        Check if the argument is a sequence of keys (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if keys is None:
            return True
        elif is_sequence(keys):
            return all(cls.is_key_instance_or_none(x, raise_on_fail=raise_on_fail) for x in keys)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys)} is not a sequence of keys (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False

    @classmethod
    @cached
    def is_record_type(cls, record_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[RecordProtocol]:
        """Check if the argument is a record type."""
        if isinstance(record_type, type) and is_record(record_type):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record_type)} is not a record type.")
        else:
            return False

    @classmethod
    @cached
    def is_record_instance(cls, record: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a record."""
        if not isinstance(record, type) and is_record(record):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record)} is not a record instance.")
        else:
            return False

    @classmethod
    @cached
    def is_record_instance_or_none(cls, record: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a record or None."""
        if record is None or (not isinstance(record, type) and is_record(record)):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record)} is not a record instance or None.")
        else:
            return False

    @classmethod
    def is_record_sequence(cls, records: Any, *, raise_on_fail: bool = True) -> TypeGuard[Sequence[RecordProtocol]]:
        """Check if the argument is a record sequence (iterable generator is not accepted)."""
        if is_sequence(records):
            return all(cls.is_record_instance(x, raise_on_fail=raise_on_fail) for x in records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(records)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def is_record_sequence_or_none(
        cls, records: Any, *, raise_on_fail: bool = True
    ) -> TypeGuard[Sequence[RecordProtocol]]:
        """
        Check if the argument is a sequence of records (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if records is None:
            return True
        elif is_sequence(records):
            return all(cls.is_record_instance_or_none(x, raise_on_fail=raise_on_fail) for x in records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(records)} is not a sequence of records (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False

    @classmethod
    @cached
    def is_key_or_record_type(cls, key_or_record_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a key or record type."""
        if isinstance(key_or_record_type, type) and is_key_or_record(key_or_record_type):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record_type)} is not a key or record type.")
        else:
            return False

    @classmethod
    @cached
    def is_key_or_record_instance(cls, key_or_record: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a key or record."""
        if not isinstance(key_or_record, type) and is_key_or_record(key_or_record):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record)} is not a key or record instance.")
        else:
            return False

    @classmethod
    @cached
    def is_key_or_record_instance_or_none(
        cls,
        key_or_record: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[KeyProtocol]:
        """Check if the argument is a key or record or None."""
        if key_or_record is None or (not isinstance(key_or_record, type) and is_key_or_record(key_or_record)):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record)} is not a key or record instance or None.")
        else:
            return False

    @classmethod
    def is_key_or_record_sequence(
        cls,
        keys_or_records: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[Sequence[KeyProtocol]]:
        """Check if the argument is a key or record sequence (iterable generator is not accepted)."""
        if is_sequence(keys_or_records):
            return all(cls.is_key_or_record_instance(x, raise_on_fail=raise_on_fail) for x in keys_or_records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys_or_records)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def is_key_or_record_sequence_or_none(
        cls, keys_or_records: Any, *, raise_on_fail: bool = True
    ) -> TypeGuard[Sequence[RecordProtocol]]:
        """
        Check if the argument is a sequence of keys or records (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if keys_or_records is None:
            return True
        elif is_sequence(keys_or_records):
            return all(cls.is_key_or_record_instance_or_none(x, raise_on_fail=raise_on_fail) for x in keys_or_records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys_or_records)} is not a sequence"
                    f"of keys or records (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False
