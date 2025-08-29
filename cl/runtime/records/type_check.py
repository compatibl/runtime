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
from typing import Mapping
from typing import Sequence
from typing import TypeGuard
from typing import cast
from cl.runtime.records.protocols import BuilderProtocol
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import is_builder
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_mapping
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename


class TypeCheck:
    """Performs runtime type checks and returns TypeGuard instance."""

    @classmethod
    def guard_sequence(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[Sequence]:
        """Confirm that the argument is an immutable sequence."""
        if obj is not None:
            if is_sequence(obj):  # TODO: Exclude mutable sequence
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not a sequence.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} is None.")
        else:
            return False

    @classmethod
    def guard_mapping(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[Mapping]:
        """Confirm that the argument is an immutable mapping."""
        if obj is not None:
            if is_mapping(obj):  # TODO: Exclude mutable mapping
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not a mapping.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} is None.")
        else:
            return False

    @classmethod
    def guard_frozen(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderProtocol]:
        """Check if the argument is frozen."""
        if is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not frozen.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} does not implement BuilderProtocol.")
        else:
            return False

    @classmethod
    def guard_frozen_or_none(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderProtocol | None]:
        """Check if the argument is frozen or None."""
        if obj is None:
            return True
        elif is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(obj)} is not frozen or None.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(obj)} does not implement BuilderProtocol and is not None.")
        else:
            return False

    @classmethod
    def guard_key_type(cls, key_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin]:
        """Check if the argument is a key type."""
        if isinstance(key_type, type) and is_key(key_type):
            if (type_name := typename(key_type)).endswith("Key"):
                return True
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a key, but its name does not end\n"
                    f"with the suffix 'Key' which is required to prevent name collusion with records."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_type)} is not a key type.")
        else:
            return False

    @classmethod
    def guard_key_instance(cls, key: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin]:
        """Check if the argument is a key instance."""
        if key is None:
            if raise_on_fail:
                raise RuntimeError("Expected a key instance but received None.")
            else:
                return False
        if not isinstance(key, type) and is_key(key):
            if (type_name := typename(key)).endswith("Key"):
                return cast(TypeGuard[KeyMixin], cls.guard_frozen(key, raise_on_fail=raise_on_fail))
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a key, but its name does not end\n"
                    f"with the suffix 'Key' which is required to prevent name collusion with records."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(key)} is not a key instance.")
        else:
            return False

    @classmethod
    def guard_key_instance_or_none(cls, key: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin | None]:
        """Check if the argument is a key instance or None."""
        if key is None:
            return True
        elif not isinstance(key, type) and is_key(key):
            if (type_name := typename(key)).endswith("Key"):
                return cast(TypeGuard[KeyMixin], cls.guard_frozen(key, raise_on_fail=raise_on_fail))
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a key, but its name does not end\n"
                    f"with the suffix 'Key' which is required to prevent name collusion with records."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(key)} is not a key instance or None.")
        else:
            return False

    @classmethod
    def guard_key_sequence(cls, keys: Any, *, raise_on_fail: bool = True) -> TypeGuard[Sequence[KeyMixin]]:
        """Check if the argument is a key sequence (iterable generator is not accepted)."""
        if is_sequence(keys):
            return all(cls.guard_key_instance(x, raise_on_fail=raise_on_fail) for x in keys)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def guard_key_sequence_or_none(
        cls, keys: Any, *, raise_on_fail: bool = True
    ) -> TypeGuard[Sequence[KeyMixin] | None] | None:
        """
        Check if the argument is a sequence of keys (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if keys is None:
            return True
        elif is_sequence(keys):
            return all(cls.guard_key_instance_or_none(x, raise_on_fail=raise_on_fail) for x in keys)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys)} is not a sequence of keys (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False

    @classmethod
    def guard_record_type(cls, record_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[RecordMixin]:
        """Check if the argument is a record type."""
        if isinstance(record_type, type) and is_record(record_type):
            if not (type_name := typename(record_type)).endswith("Key"):
                return True
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a record, but its name ends\n"
                    f"with the suffix 'Key' which is prohibited to prevent name collusion with keys."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record_type)} is not a record type.")
        else:
            return False

    @classmethod
    def guard_record_instance(cls, record: Any, *, raise_on_fail: bool = True) -> TypeGuard[RecordMixin]:
        """Check if the argument is a record."""
        if record is None:
            raise RuntimeError("Expected a record instance but received None.")
        elif not isinstance(record, type) and is_record(record):
            if not (type_name := typename(record)).endswith("Key"):
                return cast(TypeGuard[RecordMixin], cls.guard_frozen(record, raise_on_fail=raise_on_fail))
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a record, but its name ends\n"
                    f"with the suffix 'Key' which is prohibited to prevent name collusion with keys."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record)} is not a record instance.")
        else:
            return False

    @classmethod
    def guard_record_instance_or_none(cls, record: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin | None]:
        """Check if the argument is a record or None."""
        if record is None:
            return True
        elif not isinstance(record, type) and is_record(record):
            if not (type_name := typename(record)).endswith("Key"):
                return cast(TypeGuard[RecordMixin], cls.guard_frozen(record, raise_on_fail=raise_on_fail))
            elif raise_on_fail:
                raise RuntimeError(
                    f"Type {type_name} implements the required methods for a record, but its name ends\n"
                    f"with the suffix 'Key' which is prohibited to prevent name collusion with keys."
                )
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(record)} is not a record instance or None.")
        else:
            return False

    @classmethod
    def guard_record_sequence(cls, records: Any, *, raise_on_fail: bool = True) -> TypeGuard[Sequence[RecordMixin]]:
        """Check if the argument is a record sequence (iterable generator is not accepted)."""
        if is_sequence(records):
            return all(cls.guard_record_instance(x, raise_on_fail=raise_on_fail) for x in records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(records)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def guard_record_sequence_or_none(
        cls,
        records: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[Sequence[RecordMixin] | None] | None:
        """
        Check if the argument is a sequence of records (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if records is None:
            return True
        elif is_sequence(records):
            return all(cls.guard_record_instance_or_none(x, raise_on_fail=raise_on_fail) for x in records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(records)} is not a sequence of records (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False

    @classmethod
    def guard_key_or_record_type(cls, key_or_record_type: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin]:
        """Check if the argument is a key or record type."""
        if isinstance(key_or_record_type, type) and is_key_or_record(key_or_record_type):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record_type)} is not a key or record type.")
        else:
            return False

    @classmethod
    def guard_key_or_record_instance(cls, key_or_record: Any, *, raise_on_fail: bool = True) -> TypeGuard[KeyMixin]:
        """Check if the argument is a key or record."""
        if key_or_record is None:
            if raise_on_fail:
                raise RuntimeError("Expected a key or record instance but received None.")
            else:
                return False
        elif not isinstance(key_or_record, type) and is_key_or_record(key_or_record):
            return cast(TypeGuard[KeyMixin], cls.guard_frozen(key_or_record, raise_on_fail=raise_on_fail))
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record)} is not a key or record instance.")
        else:
            return False

    @classmethod
    def guard_key_or_record_instance_or_none(
        cls,
        key_or_record: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[KeyMixin | None]:
        """Check if the argument is a key or record or None."""
        if key_or_record is None:
            return True
        elif not isinstance(key_or_record, type) and is_key_or_record(key_or_record):
            return cast(TypeGuard[KeyMixin], cls.guard_frozen(key_or_record, raise_on_fail=raise_on_fail))
        elif raise_on_fail:
            raise RuntimeError(f"Parameter {typename(key_or_record)} is not a key or record instance or None.")
        else:
            return False

    @classmethod
    def guard_key_or_record_sequence(
        cls,
        keys_or_records: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[Sequence[KeyMixin]]:
        """Check if the argument is a key or record sequence (iterable generator is not accepted)."""
        if is_sequence(keys_or_records):
            return all(cls.guard_key_or_record_instance(x, raise_on_fail=raise_on_fail) for x in keys_or_records)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys_or_records)} is not a sequence (iterable generator is not accepted)."
                )
            else:
                return False

    @classmethod
    def guard_key_or_record_sequence_or_none(
        cls,
        keys_or_records: Any,
        *,
        raise_on_fail: bool = True,
    ) -> TypeGuard[Sequence[RecordMixin | None] | None]:
        """
        Check if the argument is a sequence of keys or records (iterable generator is not accepted)
        where each element can be None, and the entire sequence can also be None.
        """
        if keys_or_records is None:
            return True
        elif is_sequence(keys_or_records):
            return all(
                cls.guard_key_or_record_instance_or_none(x, raise_on_fail=raise_on_fail) for x in keys_or_records
            )
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(keys_or_records)} is not a sequence"
                    f"of keys or records (iterable generator is not accepted)\n"
                    f"where each element can be None, and the entire sequence can also be None."
                )
            else:
                return False
