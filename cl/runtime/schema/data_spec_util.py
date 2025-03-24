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
from typing import Any
from typing import Dict
from typing import Type
from uuid import UUID
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.dataclass_spec import DataclassSpec
from cl.runtime.schema.primitive_spec import PrimitiveSpec


class DataSpecUtil:
    """Helper methods for type spec."""

    _spec_dict: Dict[str, DataSpec] = {
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

    _class_dict: Dict[str, Type] | None = None
    """Dictionary of types indexed by class name."""

    @classmethod
    def from_class(cls, instance_or_type: Any) -> DataSpec:
        """Get or create type spec for the specified class."""
        type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        type_name = TypeUtil.name(type_)
        if (result := cls._spec_dict.get(type_name, None)) is not None:
            # Already created, return from spec dictionary
            return result
        else:
            # Get class for the data spec
            if dataclasses.is_dataclass(type_):
                spec_class = DataclassSpec
            else:
                raise RuntimeError(
                    f"Type {type_name} does not use one of the supported dataclass frameworks\n"
                    f"and does not have a method to generate a TypeSpec."
                )

            # Create from class, add to spec dictionary and return
            result = spec_class.from_class(type_)
            cls._spec_dict[type_name] = result
            return result
