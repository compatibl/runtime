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
from enum import Enum
from typing import Self
from frozendict import frozendict
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_mapping_type
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.protocols import is_sequence_type
from cl.runtime.records.typename import typename


@dataclass(slots=True, kw_only=True)
class TypeHint(BootstrapMixin):
    """Provides information about a type hint."""

    schema_type: type  # TODO: !! Use TypeSpec and remove subtype field?
    """Class if available, if not provided it will be looked up using the type name."""

    optional: bool | None
    """True if the type hint is a union with None, None otherwise."""

    condition: bool | None
    """True if the type hint includes T | Condition[T], None otherwise."""

    remaining: Self | None
    """Remaining chain if present, None otherwise."""

    subtype: str | None
    """Subtype (e.g., long) if specified, None otherwise."""

    def to_str(self):
        """Serialize as string in type alias format."""
        base = (
            f"{typename(self.schema_type)}[{self.remaining.to_str()}]"
            if self.remaining is not None
            else f"{typename(self.schema_type)}"
        )
        if self.condition and self.optional:
            return f"{base} | Condition[{base}] | None"
        elif self.condition:
            return f"{base} | Condition[{base}]"
        elif self.optional:
            return f"{base} | None"
        else:
            return base

    # TODO: Move to TypeHintChecks and rename to guard_
    def validate_for_primitive(self) -> None:
        """Raise an error if the type hint is not a primitive type."""
        if not is_primitive_type(self.schema_type):
            raise RuntimeError(f"{self.to_str()} is not a supported primitive type.")
        elif self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is not valid for a primitive type.")

    def validate_for_enum(self) -> None:
        """Raise an error if the type hint is not an enum."""
        if not issubclass(self.schema_type, Enum):
            raise RuntimeError(f"{self.to_str()} is not an enum type.")
        elif self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is not valid for an enum.")

    def validate_for_sequence(self) -> None:
        """Raise an error if the type hint is not a sequence."""
        if not is_sequence_type(self.schema_type):
            raise RuntimeError(f"{self.to_str()} is not a supported sequence type.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a sequence type but does not specify item type.")

    def validate_for_mapping(self) -> None:
        """Raise an error if the type hint is not a mapping."""
        if not is_mapping_type(self.schema_type):
            raise RuntimeError(f"{self.to_str()} is not a supported mapping type.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a mapping but does not specify item type.")

    def validate_for_key(self) -> None:
        """Raise an error if the type hint is not a key."""
        if not is_key_type(self.schema_type):
            raise RuntimeError(f"{self.to_str()} is not a key type.")
        elif self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a key but has additional unsupported components.")

    # TODO: Add validate_for_record, data, etc.

    @classmethod
    def for_type(
        cls,
        class_: type,
        *,
        optional: bool = None,
        condition: bool = None,
        subtype: str | None = None,
    ) -> Self:
        """Create type hint for a class with optional parameters."""
        class_name = typename(class_)
        if (subtype == "long" and class_ is not int) or (subtype == "timestamp" and class_ is not str):
            raise RuntimeError(f"Subtype {subtype} is not valid for class {class_name}.")

        return TypeHint(
            schema_type=class_,
            optional=optional,
            condition=condition,
            remaining=None,
            subtype=subtype,
        )

    @classmethod
    def for_type_alias(
        cls,
        *,
        type_alias: typing.TypeAlias,
        field_subtype: str | None = None,
        field_name: str,
        containing_type: type,
    ) -> Self:
        """
        Create type spec by parsing the type alias.

        Args:
            type_alias: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_subtype: Optional subtype such as long or timestamp, validated against type alias if provided
            field_name: Name of the field, used for error messages only and recorded into the output
            containing_type: Type that contains the field, use to resolve the generic args at runtime
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
            # Handle unions that introduce optionality and/or Condition
            type_alias_optional = None
            type_alias_condition = None

            if type_alias_origin in union_types:
                args = list(type_alias_args)

                # Detect and strip None (optional)
                if type(None) in args:
                    type_alias_optional = True
                    args.remove(type(None))

                # Detect and strip Condition[T]
                condition_arg = next(
                    (
                        a
                        for a in args
                        if typing.get_origin(a) is not None and typing.get_origin(a).__name__ == "Condition"
                    ),
                    None,
                )
                if condition_arg is not None:
                    type_alias_condition = True
                    args.remove(condition_arg)
                    (cond_inner,) = typing.get_args(condition_arg)
                else:
                    cond_inner = None

                # After removing None and Condition, there must be exactly one base type
                if len(args) != 1:
                    raise RuntimeError(
                        f"Union type hint '{cls._serialize_type_alias(type_alias)}'\n"
                        f"for field {field_name} in {typename(containing_type)} is not supported.\n"
                        f"Expected forms: 'T', 'T | None', 'T | Condition[T]', or 'T | Condition[T] | None'.\n"
                    )

                base_type = args[0]

                # If Condition is present, its inner type must match the base
                if type_alias_condition and cond_inner is not base_type:
                    raise RuntimeError(
                        f"Condition parameter does not match base type in union "
                        f"'{cls._serialize_type_alias(type_alias)}'."
                    )

                # Proceed with unwrapped base type
                type_alias = base_type
                type_alias_origin = typing.get_origin(type_alias)
                type_alias_args = typing.get_args(type_alias)

            # Parse container definitions and primitive/enum types
            is_container = type_alias_origin in supported_containers
            if is_container:
                if type_alias_origin is list:
                    if len(type_alias_args) != 1:
                        raise RuntimeError(
                            f"List type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"for field {field_name} in {typename(containing_type)} is not supported\n"
                            f"because it is not a list of elements using the syntax 'list[type]'\n"
                        )
                    # Populate container data and extract inner type alias
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type=list,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                            remaining=None,
                            subtype=None,
                        )
                    )
                elif type_alias_origin is tuple:
                    if len(type_alias_args) != 2 or type_alias_args[1] is not Ellipsis:
                        raise RuntimeError(
                            f"Tuple type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"for field {field_name} in {typename(containing_type)} is not supported\n"
                            f"because it is not a variable-length tuple using the syntax 'tuple[type, ...]'\n"
                        )
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type=tuple,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                            remaining=None,
                            subtype=None,
                        )
                    )
                elif type_alias_origin in (dict, frozendict):
                    if len(type_alias_args) != 2 or type_alias_args[0] is not str:
                        raise RuntimeError(
                            f"Type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"for field {field_name} in {typename(containing_type)} is not supported\n"
                            f"because it is not a mapping with string keys using the syntax\n"
                            f"dict[str, element_type] or frozendict[str, element_type].\n"
                        )
                    type_alias = type_alias_args[1]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type=type_alias_origin,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                            remaining=None,
                            subtype=None,
                        )
                    )
                else:
                    supported_container_names = ", ".join([typename(x) for x in supported_containers])
                    raise RuntimeError(
                        f"Container type {type_alias_origin.__name__} is not one of the supported container types "
                        f"{supported_container_names}."
                    )

                # Strip container wrapper
                type_alias_origin = typing.get_origin(type_alias)
                type_alias_args = typing.get_args(type_alias)
            else:
                # Not a container: must be a genuine type (not TypeAlias)
                if isinstance(type_alias, type):
                    if type_alias_origin is None and not type_alias_args:
                        # Validate that subtype is compatible with the schema type
                        schema_type_name = typename(type_alias)
                        if (field_subtype == "long" and schema_type_name != "int") or (
                            field_subtype == "timestamp" and schema_type_name != "str"
                        ):
                            raise RuntimeError(
                                f"Subtype '{field_subtype}' is not compatible with type {schema_type_name}"
                            )

                        # Return type hint for a primitive field
                        type_hint_tokens.append(
                            TypeHint(
                                schema_type=type_alias,
                                optional=type_alias_optional,
                                condition=type_alias_condition,
                                remaining=None,
                                subtype=field_subtype,
                            )
                        )
                    else:
                        raise RuntimeError(
                            f"Type hint {type_alias} is not supported. Supported type hints include:\n"
                            f"- a union with None (optional) with one of the supported types inside\n"
                            f"- list, tuple, dict, frozendict with one of the supported types inside\n"
                            f"- a type with build method\n"
                            f"- {', '.join(PRIMITIVE_TYPE_NAMES)}\n"
                        )

                    # Link tokens into the complete type hint
                    result = cls._link_type_hint_tokens(type_hint_tokens)
                    return result

                else:
                    raise RuntimeError(
                        f"Type hint {type_alias} is not supported. If neither optional nor a container,\n"
                        f"the type hint must be a genuine type rather than TypeAlias."
                    )

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
    def _link_type_hint_tokens(cls, type_hints: list[Self] | None) -> Self | None:
        """Convert a list of type chain tokens into a linked type chain using the 'remaining' field."""
        if type_hints:
            head, *tail = type_hints
            return TypeHint(
                schema_type=head.schema_type,
                optional=head.optional,
                condition=head.condition,
                remaining=cls._link_type_hint_tokens(tail),
                subtype=head.subtype,
            )
        else:
            return None
