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

from abc import ABC
from typing import Self
from memoization import cached
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.fields import FieldInfo

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.field_spec import FieldSpec


class PydanticMixin(BaseModel, DataMixin, ABC):
    """Implements abstract methods in DataMixin for Pydantic-based data, key or record classes."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, *args, **kwargs):
        # Support positional args in model __init__
        fields = list(self.model_fields.keys())
        for i, v in enumerate(args):
            if i < len(fields) and fields[i] not in kwargs:
                kwargs[fields[i]] = v
        super().__init__(**kwargs)

    @classmethod
    @cached
    def get_field_names(cls) -> tuple[str, ...]:
        if not issubclass(cls, BaseModel):
            raise RuntimeError(f"{typename(cls)} is derived from PydanticMixin but is not a Pydantic BaseModel.")
        return tuple(cls.model_fields.keys())

    @classmethod
    @cached
    def get_type_spec(cls) -> DataSpec:
        if not issubclass(cls, BaseModel):
            raise RuntimeError(f"{typename(cls)} is derived from PydanticMixin but is not a Pydantic BaseModel.")

        fields = [
            cls._create_field_spec(field_name, field_info, containing_type=cls)
            for field_name, field_info in cls.model_fields.items()
        ]

        return DataSpec(
            type_=cls,
            fields=fields,
        ).build()

    @classmethod
    def _create_field_spec(cls, field_name: str, field_info: FieldInfo, containing_type: type[Self]) -> FieldSpec:
        """Create FieldSpec from Pydantic model field."""

        # Pydantic fields have type_, default, required, alias, etc.
        # You can extract metadata via `field_info.field_info.extra`
        extra_metadata = getattr(field_info, "extra", {})

        result = FieldSpec.create(
            field_name=field_name,
            field_type_alias=field_info.annotation,
            containing_type=containing_type,
            field_optional=not field_info.is_required(),
            field_subtype=extra_metadata.pop("subtype", None),
            field_alias=field_info.alias or extra_metadata.pop("name", None),
            field_label=extra_metadata.pop("label", None),
            field_formatter=extra_metadata.pop("formatter", None),
            descending=extra_metadata.pop("descending", None),
        ).build()

        return result
