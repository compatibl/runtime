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

from typing import TypeGuard, Sequence, Iterable, Any

from memoization import cached
from more_itertools import consume

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.protocols import KeyProtocol, is_sequence, is_key, is_record, RecordProtocol, is_key_or_record
from cl.runtime.records.type_util import TypeUtil


class TypeGuardUtil:
    """Performs runtime type checks and returns TypeGuard instance."""
    
    @classmethod
    @cached
    def is_type_or_name(cls, type_or_name: Any, *, error_on_fail: bool = True) -> TypeGuard[type | str]:
        """Error if the argument is not a type or a string type name in PascalCase format."""
        if (
                not isinstance(type_or_name, type) and
                not (isinstance(type_or_name, str) and CaseUtil.is_pascal_case(type_or_name))
        ):
            if error_on_fail:
                raise RuntimeError(
                    f"Parameter {TypeUtil.name(type_or_name)} is not\n"
                    f"a type or a string type name in PascalCase format.")
            else:
                return False
        return True

    @classmethod
    def is_type_or_name_sequence(cls, types_or_names: Any, *, error_on_fail: bool = True) -> TypeGuard[Sequence[type | str]]:
        """
        Error if the argument is not a sequence (iterable generator is not accepted)
        of types or string type names in PascalCase format.
        """
        if is_sequence(types_or_names):
            return all(cls.is_type_or_name(type(x), error_on_fail=error_on_fail) for x in types_or_names)
        else:
            if error_on_fail:
                raise RuntimeError(
                    f"Parameter {TypeUtil.name(types_or_names)} is not a sequence\n"
                    f"(iterable generator is not accepted) of types or\n"
                    f"string type names in PascalCase format.")
            else:
                return False
        return True
    
    @classmethod
    @cached
    def is_key_type(cls, key_type: Any, *, error_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Error if the argument is not a key type."""
        if not isinstance(key_type, type) or not is_key(key_type):
            if error_on_fail:
                raise RuntimeError(f"Parameter {TypeUtil.name(key_type)} is not a key type.")
            else:
                return False
        return True

    @classmethod
    def is_key_sequence(cls, keys: Any, *, error_on_fail: bool = True) -> TypeGuard[Sequence[KeyProtocol]]:
        """Error if the argument is not a record sequence (iterable generator is not accepted)."""
        if is_sequence(keys):
            return all(cls.is_key_type(type(x), error_on_fail=error_on_fail) for x in keys)
        else:
            if error_on_fail:
                raise RuntimeError(
                    f"Parameter {TypeUtil.name(keys)} is not a sequence (iterable generator is not accepted).")
            else:
                return False
        return True

    @classmethod
    @cached
    def is_record_type(cls, record_type: Any, *, error_on_fail: bool = True) -> TypeGuard[RecordProtocol]:
        """Error if the argument is not a record type."""
        if not isinstance(record_type, type) or not is_record(record_type):
            if error_on_fail:
                raise RuntimeError(f"Parameter {TypeUtil.name(record_type)} is not a record type.")
            else:
                return False
        return True

    @classmethod
    def is_record_sequence(cls, records: Any, *, error_on_fail: bool = True) -> TypeGuard[Sequence[RecordProtocol]]:
        """Error if the argument is not a record sequence (iterable generator is not accepted)."""
        if is_sequence(records):
            return all(cls.is_record_type(type(x), error_on_fail=error_on_fail) for x in records)
        else:
            if error_on_fail:
                raise RuntimeError(
                    f"Parameter {TypeUtil.name(records)} is not a sequence (iterable generator is not accepted).")
            else:
                return False
        return True

    @classmethod
    @cached
    def is_key_or_record_type(cls, key_or_record_type: Any, *, error_on_fail: bool = True) -> TypeGuard[KeyProtocol]:
        """Error if the argument is not a record type."""
        if not isinstance(key_or_record_type, type) or not is_key_or_record(key_or_record_type):
            if error_on_fail:
                raise RuntimeError(f"Parameter {TypeUtil.name(key_or_record_type)} is not a key or record type.")
            else:
                return False
        return True

    @classmethod
    def is_key_or_record_sequence(
            cls,
            keys_or_records: Any,
            *,
            error_on_fail: bool = True,
    ) -> TypeGuard[Sequence[KeyProtocol]]:
        """Error if the argument is not a record sequence (iterable generator is not accepted)."""
        if is_sequence(keys_or_records):
            return all(cls.is_key_or_record_type(type(x), error_on_fail=error_on_fail) for x in keys_or_records)
        else:
            if error_on_fail:
                raise RuntimeError(
                    f"Parameter {TypeUtil.name(keys_or_records)} is not a sequence "
                    f"(iterable generator is not accepted).")
            else:
                return False
        return True
