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

import dataclasses
from enum import Enum
from memoization import cached
from cl.runtime.records.conditions import Condition
from cl.runtime.records.protocols import is_data_key_or_record_type, is_mixin_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.condition_spec import ConditionSpec
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_spec import TypeSpec


class TypeSchema:
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    @classmethod
    @cached
    def for_type_name(cls, type_name: str) -> TypeSpec:
        """Get or create type spec for the specified type name."""
        # Get class for the specified type name and use it to get type spec
        class_ = TypeCache.from_type_name(type_name)
        return cls.for_type(class_)

    @classmethod
    @cached
    def for_type(cls, type_: type) -> TypeSpec:
        """Get or create type spec for the specified class."""
        # TODO: ! Use get_type_spec to avoid hardcoding the list of data frameworks
        # Get class for the type spec
        if issubclass(type_, Enum):
            # Enum class
            return EnumSpec.for_type(type_)
        elif is_mixin_type(type_):
            # Mixin is a class without instance fields, use DataSpec with empty fields
            return DataSpec(
                type_name=typename(type_),
                type_=type_,
                fields=[],
            ).build()
        elif is_data_key_or_record_type(type_):  # TODO: ! Add guard methods
            # Data, key or record type other than mixin which is handled by the preceding elif
            return type_.get_type_spec()
        elif issubclass(type_, Condition):
            # Query condition type
            return ConditionSpec.for_type(type_)
        else:
            raise RuntimeError(
                f"Class {typename(type_)} implements build method but does not\n"
                f"use one of the supported dataclass frameworks and does not\n"
                f"have a method to generate type spec."
            )
