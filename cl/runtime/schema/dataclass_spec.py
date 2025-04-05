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
from dataclasses import dataclass
from typing import Type
from typing_extensions import Self
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.field_spec import FieldSpec


@dataclass(slots=True, kw_only=True)
class DataclassSpec(DataSpec):
    """Provides information about a dataclass."""

    @classmethod
    def from_class(cls, class_: Type, subtype: str | None = None) -> Self:
        """Create spec from class, subtype is not permitted."""

        # Perform checks
        type_name = TypeUtil.name(class_)
        if not dataclasses.is_dataclass(class_):
            raise RuntimeError(f"Cannot create {cls.__name__} for class {type_name} because it is not a dataclass.")
        if subtype is not None:
            raise RuntimeError(
                f"Subtype {subtype} is specified for a dataclass {type_name}.\n"
                f"Only primitive types can have subtypes."
            )

        # Create the list of enum members
        fields = [
            cls._create_field_spec(field, containing_type_name=type_name)
            for field in dataclasses.fields(class_)  # noqa: type=ignore, verified it is a dataclass above
            if not field.name.startswith("_")
        ]

        # Create the enum spec
        result = DataclassSpec(type_name=type_name, _class=class_, fields=fields)
        return result

    @classmethod
    def _create_field_spec(cls, field: dataclasses.Field, containing_type_name: str) -> FieldSpec:
        """Create field spec from dataclasses field definition."""

        # Convert dataclasses metadata to dict
        metadata = dict(field.metadata)

        result = FieldSpec.create(
            field_name=field.name,
            type_alias=field.type,
            containing_type_name=containing_type_name,
            field_optional=metadata.pop("optional", None),
            field_subtype=metadata.pop("subtype", None),
            field_alias=metadata.pop("name", None),
            field_label=metadata.pop("label", None),
            field_formatter=metadata.pop("formatter", None),
        )

        # Check that no parsed fields remained in metadata
        if len(metadata) > 0:
            raise RuntimeError(f"Unrecognized attributes in dataclass field metadata: {metadata.keys()}")

        return result
