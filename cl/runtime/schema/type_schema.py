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

from enum import Enum
from memoization import cached
from cl.runtime.records.predicates import Predicate
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_spec import TypeSpec


class TypeSchema:
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    @classmethod
    @cached
    def for_type_name(cls, type_name: str) -> TypeSpec:  # TODO: ! Remove this method?
        """Get or create type spec for the specified type name."""
        # Get class for the specified type name and use it to get type spec
        class_ = TypeInfo.from_type_name(type_name)
        return cls.for_type(class_)

    @classmethod
    @cached
    def for_type(cls, type_: type) -> TypeSpec:
        """Get or create type spec for the specified class."""
        if issubclass(type_, Enum):
            # Enum type
            return EnumSpec(type_=type_).build()
        elif is_data_key_or_record_type(type_):  # TODO: ! Use guard methods to prevent static type checker warning
            # Data, key or record type
            return type_.get_type_spec()
        elif issubclass(type_, Predicate):
            # Generic predicate type
            return DataSpec(
                type_=type_,
                fields=[],  # TODO: !!! Currently fields are not serialized, implement a custom serializer
            ).build()
        else:
            raise RuntimeError(
                f"Cannot invoke build method for type {typename(type_)} because it\n"
                f"does not use one of the supported dataclass frameworks and does not\n"
                f"have a method to generate type spec."
            )
