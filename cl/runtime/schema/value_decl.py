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

from dataclasses import dataclass
from typing import Self
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required

_VALUE_DECL_NAME_MAP: dict[str, str] = {
    "str": "String",
    "float": "Double",
    "bool": "Bool",
    "int": "Int",
    "long": "Long",
    "date": "Date",
    "time": "Time",
    "datetime": "DateTime",
    "UUID": "UUID",  # TODO: Check for support in ElementDecl
    "bytes": "Binary",
    "type": "type",
}
"""Map from Python class name to ValueDecl name."""


@dataclass(slots=True, kw_only=True)
class ValueDecl(DataclassMixin):
    """Value or atomic element declaration."""

    type_: str = required()
    """Primitive type name."""

    @classmethod
    def for_type(cls, type_: type | str) -> Self:
        """Create an instance from the specified type."""
        return cls.for_type_name(type_.__name__)

    @classmethod
    def for_type_name(cls, type_name: str) -> Self:
        """Create an instance from the specified type name."""

        runtime_name = _VALUE_DECL_NAME_MAP.get(type_name, None)
        if not runtime_name:
            raise RuntimeError(f"Primitive field type {type_name} is not supported.")
        return ValueDecl(type_=runtime_name)
