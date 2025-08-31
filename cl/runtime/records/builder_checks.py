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
from typing import TypeGuard
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.records.builder_mixin import BuilderMixin
from cl.runtime.records.protocols import is_builder
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.protocols import is_empty
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_mapping
from cl.runtime.records.protocols import is_primitive_instance
from cl.runtime.records.protocols import is_sequence
from cl.runtime.records.typename import typename


class BuilderChecks:
    """Runtime checks for the builder pattern."""

    @classmethod
    def guard_frozen(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderMixin]:
        """Check if the argument is frozen."""
        if is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(type(obj))} is not frozen.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(type(obj))} does not have build() method.")
        else:
            return False

    @classmethod
    def guard_frozen_or_none(cls, obj: Any, *, raise_on_fail: bool = True) -> TypeGuard[BuilderMixin | None]:
        """Check if the argument is frozen or None."""
        if obj is None:
            return True
        elif is_builder(obj):
            if obj.is_frozen():
                return True
            elif raise_on_fail:
                raise RuntimeError(f"Parameter of type {typename(type(obj))} is not frozen or None.")
            else:
                return False
        elif raise_on_fail:
            raise RuntimeError(f"Parameter of type {typename(type(obj))} does not have build() method and is not None.")
        else:
            return False

    @classmethod
    def is_equal(cls, data: Any, other: Any) -> bool:
        """
        Check if the arguments are equal, ignoring protected and private fields and
        mutable vs. immutable container type differences.
        """
        if is_empty(data):
            # None or an empty primitive type
            return is_empty(other)
        elif isinstance(data, float):
            # Use FloatUtil.tolerance to compare floats to avoid errors on serialization roundtrip
            return isinstance(other, float) and FloatUtil.equal(data, other)
        elif is_primitive_instance(data):
            # Exact match is required for all other types including datetime
            return is_primitive_instance(other) and data == other
        elif is_enum(data):
            return is_enum(other) and data == other
        elif is_sequence(data):
            return (
                is_sequence(other)
                and len(data) == len(other)
                and all(cls.is_equal(data_item, other_item) for data_item, other_item in zip(data, other))
            )
        elif is_mapping(data):
            return (
                is_mapping(other)
                and len(data) == len(other)
                and all(cls.is_equal(v, other.get(k)) for k, v in data.items() if not k.startswith("_"))
            )
        elif is_data_key_or_record(data):
            return (
                is_data_key_or_record(other)
                and typename(type(data)) == typename(type(other))
                and all(cls.is_equal(getattr(data, k), getattr(other, k)) for k in data.get_field_names())
            )
        else:
            raise RuntimeError(
                f"{typename(cls)} cannot compare data of type {typename(type(data))} because it is not\n"
                f"a primitive type, enum, data, key or record class or a supported container of these types."
            )

    @classmethod
    def guard_equal(cls, data: Any, other: Any, *, raise_on_fail: bool = True) -> bool:
        """
        Check if the arguments are equal, ignoring protected and private fields and
        mutable vs. immutable container type differences.
        """
        if result := cls.is_equal(data, other):
            return True
        elif raise_on_fail:
            raise RuntimeError(f"Data objects are not equal.\nFirst:\n{data}\nSecond:\n{other}\n")
        else:
            return False
