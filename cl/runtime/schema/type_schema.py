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
import datetime as dt
from enum import Enum
from types import ModuleType
from typing import Mapping
from typing import cast
from uuid import UUID
from cl.runtime.records.protocols import DataProtocol
from cl.runtime.records.protocols import is_data_key_or_record
from cl.runtime.records.typename import typename
from cl.runtime.schema.dataclass_spec import DataclassSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.no_slots_spec import NoSlotsSpec
from cl.runtime.schema.primitive_spec import PrimitiveSpec
from cl.runtime.schema.type_cache import TypeCache
from cl.runtime.schema.type_spec import TypeSpec


class TypeSchema:
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    _spec_dict: dict[str, TypeSpec] = {
        "str": PrimitiveSpec.from_class(str),
        "float": PrimitiveSpec.from_class(float),
        "bool": PrimitiveSpec.from_class(bool),
        "int": PrimitiveSpec.from_class(int),
        "long": PrimitiveSpec.from_class(int, subtype="long"),
        "date": PrimitiveSpec.from_class(dt.date),
        "time": PrimitiveSpec.from_class(dt.time),
        "datetime": PrimitiveSpec.from_class(dt.datetime),
        "UUID": PrimitiveSpec.from_class(UUID),
        "timestamp": PrimitiveSpec.from_class(UUID, subtype="timestamp"),
        "bytes": PrimitiveSpec.from_class(float),
    }
    """Dictionary of type specs indexed by type name and initialized with primitive types."""

    _class_dict: Mapping[str, type] | None = None
    """Dictionary of types indexed by class name."""

    _modules: tuple[ModuleType, ...] | None = None
    """Modules from the packages specified in the settings."""

    _packages: tuple[str, ...] | None = None
    """Packages specified in the settings."""

    @classmethod
    def for_type_name(cls, type_name: str) -> TypeSpec:
        """Get or create type spec for the specified type name."""
        if (result := cls._spec_dict.get(type_name, None)) is not None:
            # Already created, return from spec dictionary
            return result
        else:
            # Get class for the specified type name and use it to get type spec
            class_ = TypeCache.from_type_name(type_name)
            return cls.for_class(class_)

    @classmethod
    def for_class(cls, class_: type) -> TypeSpec:
        """Get or create type spec for the specified class."""
        type_name = typename(class_)
        if (result := cls._spec_dict.get(type_name, None)) is not None:
            # Already created, return from spec dictionary
            return result
        else:
            # Get class for the specified type name
            class_ = TypeCache.from_type_name(type_name)

            # TODO: Use mapping records to avoid hardcoding the list of data frameworks
            # Get class for the type spec
            if issubclass(class_, Enum):
                # Enum class
                spec_class = EnumSpec
            elif dataclasses.is_dataclass(class_):
                # Uses dataclasses
                spec_class = DataclassSpec
            elif is_data_key_or_record(class_) and not cast(DataProtocol, class_).get_field_names():
                # Base class of data, key or record with no slots
                spec_class = NoSlotsSpec
            else:
                raise RuntimeError(
                    f"Class {typename(class_)} implements build method but does not\n"
                    f"use one of the supported dataclass frameworks and does not\n"
                    f"have a method to generate type spec."
                )

            # Create from class, add to spec dictionary and return
            result = spec_class.from_class(class_)
            cls._spec_dict[type_name] = result
            return result
