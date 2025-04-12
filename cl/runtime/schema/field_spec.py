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

import typing
from dataclasses import dataclass
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.frozen_data import FrozenData
from cl.runtime.schema.type_hint import TypeHint


@dataclass(slots=True, kw_only=True, frozen=True)
class FieldSpec(FrozenData):
    """Provides information about a field in DataSpec, use frozen attribute."""

    field_name: str
    """Field name (must be unique within the class)."""

    type_hint: TypeHint
    """
    Chain of nested type hints, each item has format 'type_name' or 'type_name | None'
    where type_name may refer to a container, slotted type, or primitive type.
    """

    _class: type
    """The inner data class or primitive class inside the nested containers."""

    def get_class(self) -> type:
        """The inner data class or primitive class inside the nested containers."""
        return self._class

    @classmethod
    def create(
        cls,
        *,
        field_name: str,
        type_alias: typing.TypeAlias,
        field_optional: bool | None = None,
        field_subtype: str | None = None,
        field_alias: str | None = None,
        field_label: str | None = None,
        field_formatter: str | None = None,
        containing_type_name: str,
    ) -> Self:
        """
        Create type spec by parsing the type hint.

        Args:
            field_name: Name of the field, used for error messages only and recorded into the output
            type_alias: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_subtype: Optional subtype from field metadata such as long or timestamp
            field_optional: Optional flag from field metadata, cross check against type hint if not None
            field_alias: Optional name alias from field metadata, field name is used when not specified
            field_label: Optional label from field metadata, CaseUtil.titleize is used when not specified
            field_formatter: Optional formatter from field metadata, standard formatting is used when not specified
            containing_type_name: Name of the class that contains the field
        """

        # Create type hint object from type alias
        type_hint = TypeHint.for_type_alias(
            type_alias=type_alias,
            field_subtype=field_subtype,
            where_msg=f"for field {field_name} in {containing_type_name}",
        )

        if field_alias is not None:
            raise RuntimeError(f"Specifying 'field_alias' is not yet supported.")
        if field_label is not None:
            raise RuntimeError(f"Specifying 'field_label' is not yet supported.")
        if field_formatter is not None:
            raise RuntimeError(f"Specifying 'field_formatter' in schema is not yet supported.")

        # Validate optional flag if provided
        if field_optional is not None and field_optional != type_hint.optional:
            if field_optional is True:
                raise RuntimeError(
                    f"Field {containing_type_name}.{field_name} uses '= optional()'\n"
                    f"but type hint is not a union with None: {type_hint.to_str()}"
                )
            if field_optional is False:
                raise RuntimeError(
                    f"Field {containing_type_name}.{field_name} uses '= required()'\n"
                    f"but type hint is a union with None: {type_hint.to_str()}"
                )

        result = cls(
            field_name=field_name,
            type_hint=type_hint,
            _class=type_alias,
        )
        return result
