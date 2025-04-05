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
from typing import List
from dataclasses import dataclass
from typing import Type
from uuid import UUID

from frozendict import frozendict
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.frozen_data_mixin import FrozenDataMixin
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES, SEQUENCE_TYPE_NAMES, MAPPING_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True, frozen=True)
class TypeHint(FrozenDataMixin):
    """Provides information about a type hint."""

    schema_type_name: str
    """Type name in the schema."""

    schema_class: Type | None = None
    """Class if available, if not provided it will be looked up using the type name."""

    optional: bool
    """Optional flag, True if the type hint is a union with None, None otherwise."""

    remaining: Self | None = None
    """Remaining chain if present, None otherwise."""

    def get_schema_class_or_none(self) -> Type:
        """Return schema class if available, otherwise return None."""
        return self.schema_class

    def to_str(self):
        """Serialize as string in type alias format."""
        if self.remaining is not None:
            if self.optional:
                return f"{self.schema_type_name}[{self.remaining.to_str()}] | None"
            else:
                return f"{self.schema_type_name}[{self.remaining.to_str()}]"
        else:
            if self.optional:
                return f"{self.schema_type_name} | None"
            else:
                return f"{self.schema_type_name}"

    def validate_for_sequence(self) -> None:
        """Raise an error if the type hint is not a sequence."""
        if not self.schema_type_name in SEQUENCE_TYPE_NAMES:
            raise RuntimeError(f"The data is a sequence but type hint {self.to_str()} does not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a sequence type but does not specify item type.")

    def validate_for_mapping(self) -> None:
        """Raise an error if the type hint is not a mapping."""
        if not self.schema_type_name in MAPPING_TYPE_NAMES:
            raise RuntimeError(f"The data is a mapping but type hint {self.to_str()} does not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a mapping but does not specify item type.")

    @classmethod
    def for_class(
            cls,
            class_: Type,
            *,
            optional: bool = False,
            schema_type_name: str | None = None,
    ) -> Self:
        """Create type hint for a class with optional parameters."""

        class_name = TypeUtil.name(class_)
        if (
                schema_type_name is None or
                (schema_type_name == "long" and class_ is int) or
                (schema_type_name == "timestamp" and class_ is UUID)
        ):
            # Validate and use subtype if specified
            schema_type_name = class_name
        elif schema_type_name != class_name:
            # Otherwise use class name
            raise RuntimeError(f"Subtype {schema_type_name} is not valid for class {class_name}.")

        return cls(
            schema_type_name=schema_type_name,
            schema_class=class_,
            optional=optional,
        )

    @classmethod
    def for_type_alias(
        cls,
        *,
        type_alias: typing.TypeAlias,
        field_subtype: str | None = None,
        where_msg: str,
    ) -> Self:
        """
        Create type spec by parsing the type alias.

        Args:
            type_alias: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_subtype: Optional subtype such as long or timestamp, validated against type alias if provided
            where_msg: Description of where the type alias is encountered for error messages only
        """

        # Variables to store the result of type hint parsing
        type_hint_tokens = []

        # Get origin and args of the field type
        type_alias_origin = typing.get_origin(type_alias)
        type_alias_args = typing.get_args(type_alias)

        # There are two possible forms of origin for optional, typing.Union and types.UnionType
        union_types = [types.UnionType, typing.Union]
        supported_containers = [list, tuple, dict, frozendict]
        while True:
            # There are two possible forms of origin for optional, typing.Union and types.UnionType
            if type_alias_optional := type_alias_origin in union_types:
                # Union with None is the only permitted Union type
                if len(type_alias_args) != 2 or type_alias_args[1] is not type(None):
                    raise RuntimeError(
                        f"Union type hint '{cls._serialize_type_alias(type_alias)}'\n"
                        f"{where_msg} is not supported\n"
                        f"because it is not an optional value using the syntax 'Type | None'\n"
                    )

                # Get type information without None
                type_alias = type_alias_args[0]
                type_alias_origin = typing.get_origin(type_alias)
                type_alias_args = typing.get_args(type_alias)  # TODO: Add a check

            if is_container := type_alias_origin in supported_containers:
                # Parse container definition and add container types
                if type_alias_origin is list:
                    # Perform additional checks for list
                    if len(type_alias_args) != 1:
                        raise RuntimeError(
                            f"List type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"{where_msg} is not supported\n"
                            f"because it is not a list of elements using the syntax 'List[Type]'\n"
                        )
                    # Populate container data and extract the inner type alias
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(TypeHint(
                        schema_type_name="list",
                        schema_class=list,
                        optional=type_alias_optional,
                    ))
                elif type_alias_origin is tuple:
                    # Perform additional checks for tuple
                    if len(type_alias_args) != 2 or type_alias_args[1] is not Ellipsis:
                        raise RuntimeError(
                            f"Tuple type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"{where_msg} is not supported\n"
                            f"because it is not a variable-length tuple using the syntax 'Tuple[Type, ...]'\n"
                        )
                    # Populate container data and extract the inner type alias
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(TypeHint(
                        schema_type_name="tuple",
                        schema_class=tuple,
                        optional=type_alias_optional,
                    ))
                elif type_alias_origin is dict:
                    # Perform additional checks for dict
                    if len(type_alias_args) != 2 or type_alias_args[0] is not str:
                        raise RuntimeError(
                            f"Dict type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"{where_msg} is not supported\n"
                            f"because it is not a dictionary with string keys using the syntax 'Dict[str, Type]'\n"
                        )
                    # Populate container data and extract the inner type alias
                    type_alias = type_alias_args[1]
                    type_hint_tokens.append(TypeHint(
                        schema_type_name="dict",
                        schema_class=dict,
                        optional=type_alias_optional,
                    ))
                else:
                    supported_container_names = ", ".join([TypeUtil.name(x) for x in supported_containers])
                    raise RuntimeError(
                        f"Container type {type_alias_origin.__name__} is not one of the supported container types "
                        f"{supported_container_names}."
                    )

                # Strip container information from the type alias to get the type of value inside the container
                type_alias_origin = typing.get_origin(type_alias)
                type_alias_args = typing.get_args(type_alias)

            else:
                # If not optional and not a container, the remaining part of the type hint
                # must be a genuine inner type remains without wrappers from typing.
                # Check using isinstance(type_alias, type) which will return False for a type alias.
                if isinstance(type_alias, type):
                    if type_alias_origin is None and not type_alias_args:

                        # Add the ultimate inner type inside nested containers to the last type chain item
                        schema_type_name = TypeUtil.name(type_alias)

                        # Apply field subtype from metadata if specified
                        if field_subtype is None or field_subtype == schema_type_name:
                            type_hint_tokens.append(TypeHint(
                                schema_type_name=schema_type_name,
                                schema_class=type_alias,
                                optional=type_alias_optional,
                            ))
                        elif field_subtype == "long":
                            if schema_type_name == "int":
                                type_hint_tokens.append(TypeHint(
                                    schema_type_name="long",
                                    schema_class=int,
                                    optional=type_alias_optional,
                                ))
                            else:
                                raise RuntimeError(f"Subtype 'long' is not valid for type hint {type_alias}")
                        elif field_subtype == "timestamp":
                            if schema_type_name == "UUID":
                                type_hint_tokens.append(TypeHint(
                                    schema_type_name="timestamp",
                                    schema_class=UUID,
                                    optional=type_alias_optional,
                                ))
                            else:
                                raise RuntimeError(f"Subtype 'timestamp' is not valid for type hint {type_alias}")
                        else:
                            raise RuntimeError(
                                f"Type name {field_subtype} is not valid for class {schema_type_name}."
                            )
                    else:
                        raise RuntimeError(
                            f"Type hint {type_alias} is not supported. Supported type hints include:\n"
                            f"- a union with None (optional) with one of the supported types inside\n"
                            f"- list, tuple, dict, frozendict with one of the supported types inside\n"
                            f"- a type with build method\n"
                            f"- {', '.join(PRIMITIVE_CLASS_NAMES)}\n"
                        )

                    # Link tokens into the complete type hint
                    result = cls._link_type_hint_tokens(type_hint_tokens)
                    return result

    @classmethod
    def _serialize_type_alias(cls, alias: typing.Any) -> str:
        """Serialize a type alias without namespaces."""
        if hasattr(alias, "__origin__"):
            origin = alias.__origin__.__name__
            args = ", ".join(cls._serialize_type_alias(arg) for arg in alias.__args__)
            return f"{origin}[{args}]"
        elif hasattr(alias, "__name__"):
            return alias.__name__
        return str(alias)

    @classmethod
    def _link_type_hint_tokens(cls, type_hints: List[Self] | None) -> Self | None:
            """Convert a list of type chain tokens into a linked type chain using the 'remaining' field."""
            if type_hints:
                head, *tail = type_hints
                return TypeHint(
                    schema_type_name=head.schema_type_name,
                    schema_class=head.schema_class,
                    optional=head.optional,
                    remaining=cls._link_type_hint_tokens(tail)
                )
            else:
                return None