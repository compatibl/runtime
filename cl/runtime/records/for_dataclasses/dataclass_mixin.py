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
from abc import ABC
from typing import Self

from memoization import cached

from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.data_spec import DataSpec
from cl.runtime.schema.field_spec import FieldSpec
from cl.runtime.serializers.slots_util import SlotsUtil


class DataclassMixin(DataMixin, ABC):
    """Implements abstract methods in DataMixin for dataclass-based data, key or record classes."""

    __slots__ = ()

    @classmethod
    @cached
    def get_field_names(cls) -> tuple[str, ...]:
        return SlotsUtil.get_field_names(cls)  # TODO: !!!!!! Replace with get_type_spec

    @classmethod
    @cached
    def get_type_spec(cls) -> DataSpec:

        if not dataclasses.is_dataclass(cls):
            raise RuntimeError(f"{typename(cls)} is derived from DataclassMixin but has no @dataclass decorator.")

        # Create the list of field specs
        fields = [
            cls._create_field_spec(field, containing_type=cls)  # noqa: type=ignore
            for field in dataclasses.fields(cls)  # noqa: type=ignore
            if not field.name.startswith("_")
        ]

        return DataSpec(
            type_name=typename(cls),
            type_=cls,
            fields=fields,
        ).build()

    @classmethod
    def _create_field_spec(cls, field: dataclasses.Field, containing_type: type[Self]) -> FieldSpec:
        """Create FieldSpec from dataclasses Field."""

        # Convert dataclasses metadata to dict
        metadata_dict = dict(field.metadata)

        # Create field spec including metadata
        result = FieldSpec.create(
            field_name=field.name,
            field_type_alias=field.type,
            containing_type=containing_type,
            field_optional=metadata_dict.pop("optional", None),
            field_subtype=metadata_dict.pop("subtype", None),
            field_alias=metadata_dict.pop("name", None),  # TODO: ! Add support for name
            field_label=metadata_dict.pop("label", None),  # TODO: ! Add support for label
            field_formatter=metadata_dict.pop("formatter", None),  # TODO: ! Add support for formatter
        )

        # Check that no keys remained in metadata after using all known keys
        if len(metadata_dict) > 0:
            unused_metadata_str = "\n".join(f"{k}:{v}" for k, v in metadata_dict)
            raise RuntimeError(f"Unrecognized keys in dataclass field metadata:\n{unused_metadata_str}")
        return result
