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

import types
import typing
from dataclasses import dataclass
from typing import Tuple
from typing import Type
from frozendict import frozendict
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.frozen_data_mixin import FrozenDataMixin
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True, frozen=True)
class FieldSpec(FrozenDataMixin):
    """Provides information about a field in DataSpec, use frozen attribute."""

    field_name: str
    """Field name (must be unique within the class)."""

    type_hint: str
    """Type hint from which the type chain was created as string."""

    type_chain: Tuple[Tuple[str, Type, bool], ...]
    """
    Chain of nested type hints, each item has format 'type_name' or 'type_name | None'
    where type_name may refer to a container, slotted type, or primitive type.
    """

    _class: Type
    """The inner data class or primitive class inside the nested containers."""

    def get_class(self) -> Type:
        """The inner data class or primitive class inside the nested containers."""
        return self._class

    @classmethod
    def create(
        cls,
        *,
        field_name: str,
        type_hint: typing.TypeAlias,
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
            type_hint: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_subtype: Optional subtype from field metadata such as long or timestamp
            field_optional: Optional flag from field metadata, cross check against type hint if not None
            field_alias: Optional name alias from field metadata, field name is used when not specified
            field_label: Optional label from field metadata, CaseUtil.titleize is used when not specified
            field_formatter: Optional formatter from field metadata, standard formatting is used when not specified
            containing_type_name: Name of the class that contains the field
        """

        # Variables to store the result of type hint parsing
        root_type_hint_str = cls._serialize_type_hint(type_hint)
        root_optional = None
        type_chain = []

        # Get origin and args of the field type
        type_hint_origin = typing.get_origin(type_hint)
        type_hint_args = typing.get_args(type_hint)

        # There are two possible forms of origin for optional, typing.Union and types.UnionType
        union_types = [types.UnionType, typing.Union]
        supported_containers = [list, tuple, dict, frozendict]
        while True:
            # There are two possible forms of origin for optional, typing.Union and types.UnionType
            type_hint_optional = type_hint_origin in union_types

            # Assign to True or False for the outer hit only
            if root_optional is None:
                root_optional = type_hint_optional

            if type_hint_optional:
                # Union with None is the only permitted Union type
                if len(type_hint_args) != 2 or type_hint_args[1] is not type(None):
                    raise RuntimeError(
                        f"Union type hint '{cls._serialize_type_hint(type_hint)}'\n"
                        f"for field {field_name} in {containing_type_name} is not supported\n"
                        f"because it is not an optional value using the syntax 'Type | None'\n"
                    )

                # Get type information without None
                type_hint = type_hint_args[0]
                type_hint_origin = typing.get_origin(type_hint)
                type_hint_args = typing.get_args(type_hint)  # TODO: Add a check

            if is_container := type_hint_origin in supported_containers:
                # Parse container definition and add container types to type_chain
                if type_hint_origin is list:
                    # Perform additional checks for list
                    if len(type_hint_args) != 1:
                        raise RuntimeError(
                            f"List type hint '{cls._serialize_type_hint(type_hint)}'\n"
                            f"for field {field_name} in {containing_type_name} is not supported\n"
                            f"because it is not a list of elements using the syntax 'List[Type]'\n"
                        )
                    # Populate container data and extract the inner type_hint
                    type_hint = type_hint_args[0]
                    type_chain.append("list | None" if type_hint_optional else "list")
                elif type_hint_origin is tuple:
                    # Perform additional checks for tuple
                    if len(type_hint_args) != 2 or type_hint_args[1] is not Ellipsis:
                        raise RuntimeError(
                            f"Tuple type hint '{cls._serialize_type_hint(type_hint)}'\n"
                            f"for field {field_name} in {containing_type_name} is not supported\n"
                            f"because it is not a variable-length tuple using the syntax 'Tuple[Type, ...]'\n"
                        )
                    # Populate container data and extract the inner type_hint
                    type_hint = type_hint_args[0]
                    type_chain.append("tuple | None" if type_hint_optional else "tuple")
                elif type_hint_origin is dict:
                    # Perform additional checks for dict
                    if len(type_hint_args) != 2 or type_hint_args[0] is not str:
                        raise RuntimeError(
                            f"Dict type hint '{cls._serialize_type_hint(type_hint)}'\n"
                            f"for field {field_name} in {containing_type_name} is not supported\n"
                            f"because it is not a dictionary with string keys using the syntax 'Dict[str, Type]'\n"
                        )
                    # Populate container data and extract the inner type_hint
                    type_hint = type_hint_args[1]
                    type_chain.append("dict | None" if type_hint_optional else "dict")
                else:
                    supported_container_names = ", ".join([TypeUtil.name(x) for x in supported_containers])
                    raise RuntimeError(
                        f"Container type {type_hint_origin.__name__} is not one of the supported container types "
                        f"{supported_container_names}."
                    )

                # Strip container information from type_hint to get the type of value inside the container
                type_hint_origin = typing.get_origin(type_hint)
                type_hint_args = typing.get_args(type_hint)

            else:
                # If not optional and not a container, the remaining part of the type hint
                # must be a genuine inner type remains without wrappers from typing.
                # Check using isinstance(type_hint, type) which will return False for a type alias.
                if isinstance(type_hint, type):
                    if type_hint_origin is None and not type_hint_args:
                        # Add the ultimate inner type inside nested containers to the last type chain item
                        type_name = TypeUtil.name(type_hint)
                        type_chain.append(f"{type_name} | None" if type_hint_optional else type_name)
                    else:
                        raise RuntimeError(
                            f"Type hint {type_hint} is not supported. Supported type hints include:\n"
                            f"- a union with None (optional) with one of the supported types inside\n"
                            f"- list, tuple, dict, frozendict with one of the supported types inside\n"
                            f"- a type with build method\n"
                            f"- {', '.join(PRIMITIVE_CLASS_NAMES)}\n"
                        )

                    # Apply field subtype from metadata
                    if field_subtype is not None:
                        if field_subtype == "long":
                            if type_chain == ["int"]:
                                type_chain = ["long"]
                            elif type_chain == ["int | None"]:
                                type_chain = ["long | None"]
                            else:
                                raise RuntimeError(f"Subtype 'long' is not valid for type hint {type_hint}")
                        elif field_subtype == "timestamp":
                            if type_chain == ["UUID"]:
                                type_chain = ["timestamp"]
                            elif type_chain == ["UUID | None"]:
                                type_chain = ["timestamp | None"]
                            else:
                                raise RuntimeError(f"Subtype 'timestamp' is not valid for type hint {type_hint}")
                        else:
                            raise RuntimeError(
                                f"Subtype {field_subtype} is not valid, supported subtypes are 'long' and 'timestamp'."
                            )

                    # TODO: Check optional flag from metadata
                    if field_optional is not None and field_optional != root_optional:
                        if field_optional is True:
                            raise RuntimeError(
                                f"Field {containing_type_name}.{field_name} uses '= optional()'\n"
                                f"but type hint is not a union with None: {root_type_hint_str}"
                            )
                        if field_optional is False:
                            raise RuntimeError(
                                f"Field {containing_type_name}.{field_name} uses '= required()'\n"
                                f"but type hint is a union with None: {root_type_hint_str}"
                            )
                    if field_alias is not None:
                        raise RuntimeError(f"Specifying 'field_alias' is not yet supported.")
                    if field_label is not None:
                        raise RuntimeError(f"Specifying 'field_label' is not yet supported.")
                    if field_formatter is not None:
                        raise RuntimeError(f"Specifying 'field_formatter' in schema is not yet supported.")

                    # Create the field spec and return which ends the while True loop
                    result = cls(
                        field_name=field_name,
                        type_hint=root_type_hint_str,
                        type_chain=tuple(type_chain),
                        _class=type_hint,
                    )
                    return result

    @classmethod
    def _serialize_type_hint(cls, alias: typing.Any) -> str:
        """Serialize a type alias without namespaces."""
        if hasattr(alias, "__origin__"):
            origin = alias.__origin__.__name__
            args = ", ".join(cls._serialize_type_hint(arg) for arg in alias.__args__)
            return f"{origin}[{args}]"
        elif hasattr(alias, "__name__"):
            return alias.__name__
        return str(alias)
