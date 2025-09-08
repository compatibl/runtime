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
from typing import Self
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint


@dataclass(slots=True, kw_only=True)
class FieldSpec(BootstrapMixin):
    """Provides information about a field in DataSpec, use frozen attribute."""

    field_name: str
    """Field name (must be unique within the class)."""

    field_type_hint: TypeHint
    """
    Chain of nested type hints, each item has format 'type_name' or 'type_name | None'
    where type_name may refer to a container, slotted type, or primitive type.
    """

    field_order: int = 1
    """Field order in query definition, 1 for ascending (default), -1 for descending."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.field_order not in (1, -1):
            raise RuntimeError(
                f"Field order can only be 1 for ascending or -1 for descending,\n"
                f"the value of {self.field_order} for field {self.field_name} is not valid."
                )

    @classmethod
    def create(
        cls,
        *,
        field_name: str,
        field_type_alias: typing.TypeAlias,
        field_optional: bool | None = None,
        field_subtype: str | None = None,
        field_alias: str | None = None,
        field_label: str | None = None,
        field_formatter: str | None = None,
        containing_type: type,
    ) -> Self:
        """
        Create type spec by parsing the type hint.

        Args:
            field_name: Name of the field, used for error messages only and recorded into the output
            field_type_alias: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_subtype: Optional subtype from field metadata such as long or timestamp
            field_optional: Optional flag from field metadata, cross check against type hint if not None
            field_alias: Optional name alias from field metadata, field name is used when not specified
            field_label: Optional label from field metadata, CaseUtil.titleize is used when not specified
            field_formatter: Optional formatter from field metadata, standard formatting is used when not specified
            containing_type: Type that contains the field, use to resolve the generic args at runtime
        """

        # Create type hint object from type alias
        field_type_hint = TypeHint.for_type_alias(
            type_alias=field_type_alias,
            field_subtype=field_subtype,
            field_name=field_name,
            containing_type=containing_type,
        )

        if field_alias is not None:
            raise RuntimeError(f"Specifying 'field_alias' is not yet supported.")
        if field_label is not None:
            raise RuntimeError(f"Specifying 'field_label' is not yet supported.")
        if field_formatter is not None:
            raise RuntimeError(f"Specifying 'field_formatter' in schema is not yet supported.")

        # Validate optional flag if provided
        if field_optional is not None and field_optional != bool(field_type_hint.optional):
            if field_optional:
                raise RuntimeError(
                    f"Field {typename(containing_type)}.{field_name} uses '= optional()'\n"
                    f"but type hint is not a union with None: {field_type_hint.to_str()}"
                )
            if not field_optional:
                raise RuntimeError(
                    f"Field {typename(containing_type)}.{field_name} uses '= required()'\n"
                    f"but type hint is a union with None: {field_type_hint.to_str()}"
                )

        result = cls(
            field_name=field_name,
            field_type_hint=field_type_hint,
        )
        return result
