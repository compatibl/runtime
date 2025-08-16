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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TObj
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_key_or_record
from cl.runtime.records.protocols import is_record
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename


class TypeCheck:
    """Performs runtime type checks and returns TypeGuard instance."""

    @classmethod
    @cached
    def is_same_type(
        cls, instance_or_type: Any, expected_type: type[TObj], *, raise_on_fail: bool = True
    ) -> TypeGuard[TObj]:
        """Check if the type of 'instance_or_type' is 'expected_type', subclasses are not permitted."""
        # Accept instance or type
        type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        if not type_ == expected_type:
            if raise_on_fail:
                raise RuntimeError(f"Received type {typename(type_)} where {typename(expected_type)} is expected.")
            else:
                return False
        else:
            return True

    @classmethod
    @cached
    def is_same_type_or_subtype(
        cls, instance_or_type: Any, expected_type: type[TObj], *, raise_on_fail: bool = True
    ) -> TypeGuard[TObj]:
        """Check if the type of 'instance_or_type' is the same type or subtype (subclass) of 'expected_type'."""
        # Accept instance or type
        type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        if not issubclass(type_, expected_type):
            if raise_on_fail:
                raise RuntimeError(f"Received type {typename(type_)} where {typename(expected_type)} is expected.")
            else:
                return False
        else:
            return True

    @classmethod
    @cached
    def is_type_or_name(cls, type_or_name: Any, *, raise_on_fail: bool = True) -> TypeGuard[type | str]:
        """Check if the argument is not a type or a string type name in PascalCase format."""
        if not isinstance(type_or_name, type) and not (
            isinstance(type_or_name, str) and CaseUtil.is_pascal_case(type_or_name)
        ):
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(type_or_name)} is not\n" f"a type or a string type name in PascalCase format."
                )
            else:
                return False
        return True

    @classmethod
    def is_type_or_name_sequence(
        cls, types_or_names: Any, *, raise_on_fail: bool = True
    ) -> TypeGuard[Sequence[type | str]]:
        """
        Check if the argument is not a sequence (iterable generator is not accepted)
        of types or string type names in PascalCase format.
        """
        if is_sequence(types_or_names):
            return all(cls.is_type_or_name(x, raise_on_fail=raise_on_fail) for x in types_or_names)
        else:
            if raise_on_fail:
                raise RuntimeError(
                    f"Parameter {typename(types_or_names)} is not a sequence\n"
                    f"(iterable generator is not accepted) of types or\n"
                    f"string type names in PascalCase format."
                )
            else:
                return False

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
        """Check if the argument is a key."""
        if not isinstance(key, type) and is_key(key):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(key)} is not a key instance.")
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
