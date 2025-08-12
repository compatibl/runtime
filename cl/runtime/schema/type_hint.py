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
from typing import List
from typing import Self
from uuid import UUID
from frozendict import frozendict
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.protocols import MAPPING_TYPE_NAMES
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import PRIMITIVE_TYPE_NAMES
from cl.runtime.records.protocols import SEQUENCE_TYPE_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class TypeHint(BootstrapMixin):
    """Provides information about a type hint."""

    schema_type_name: str
    """Type name in the schema."""

    _schema_class: type
    """Class if available, if not provided it will be looked up using the type name."""

    optional: bool | None = None
    """True if the type hint is a union with None, None otherwise."""

    condition: bool | None = None
    """True if the type hint includes T | Condition[T], None otherwise."""

    remaining: Self | None = None
    """Remaining chain if present, None otherwise."""

    def get_schema_class(self) -> type:
        """Return schema class."""
        return self._schema_class

    def to_str(self):
        """Serialize as string in type alias format."""
        base = (
            f"{self.schema_type_name}[{self.remaining.to_str()}]"
            if self.remaining is not None
            else f"{self.schema_type_name}"
        )
        if self.condition and self.optional:
            return f"{base} | Condition[{base}] | None"
        elif self.condition:
            return f"{base} | Condition[{base}]"
        elif self.optional:
            return f"{base} | None"
        else:
            return base

    def validate_for_primitive(self) -> None:
        """Raise an error if the type hint is not a primitive type."""
        if not self.schema_type_name in PRIMITIVE_TYPE_NAMES:
            raise RuntimeError(f"{self.to_str()} is not a supported primitive type.")
        elif self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is not valid for a primitive type.")

    def validate_for_enum(self) -> None:
        """Raise an error if the type hint is not an enum."""
        if not issubclass(self._schema_class, Enum):
            raise RuntimeError(f"{self.to_str()} is not compatible with enum value.")
        elif self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is not valid for an enum.")

    def validate_for_sequence(self) -> None:
        """Raise an error if the type hint is not a sequence."""
        if not self.schema_type_name in SEQUENCE_TYPE_NAMES:
            raise RuntimeError(f"The data is a sequence but type hint {self.to_str()} is not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a sequence type but does not specify item type.")

    def validate_for_mapping(self) -> None:
        """Raise an error if the type hint is not a mapping."""
        if not self.schema_type_name in MAPPING_TYPE_NAMES:
            raise RuntimeError(f"The data is a mapping but the type hint {self.to_str()} is not.")
        elif not self.remaining:
            raise RuntimeError(f"The type hint {self.to_str()} is a mapping but does not specify item type.")

    @classmethod
    def for_class(
        cls,
        class_: type,
        *,
        optional: bool = None,
        condition: bool = None,
        schema_type_name: str | None = None,
    ) -> Self:
        """Create type hint for a class with optional parameters."""

        class_name = TypeUtil.name(class_)
        if (
            schema_type_name is None
            or (schema_type_name == "long" and class_ is int)
            or (schema_type_name == "timestamp" and class_ is UUID)
        ):
            # Validate and use subtype if specified
            schema_type_name = class_name
        elif schema_type_name != class_name:
            # Otherwise use class name
            raise RuntimeError(f"Subtype {schema_type_name} is not valid for class {class_name}.")

        return cls(
            schema_type_name=schema_type_name,
            _schema_class=class_,
            optional=optional,
            condition=condition,
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
                        f"for field {field_name} in {TypeUtil.name(containing_type)} is not supported.\n"
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
                            f"for field {field_name} in {TypeUtil.name(containing_type)} is not supported\n"
                            f"because it is not a list of elements using the syntax 'List[type]'\n"
                        )
                    # Populate container data and extract inner type alias
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type_name="list",
                            _schema_class=list,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                        )
                    )
                elif type_alias_origin is tuple:
                    if len(type_alias_args) != 2 or type_alias_args[1] is not Ellipsis:
                        raise RuntimeError(
                            f"Tuple type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"for field {field_name} in {TypeUtil.name(containing_type)} is not supported\n"
                            f"because it is not a variable-length tuple using the syntax 'Tuple[type, ...]'\n"
                        )
                    type_alias = type_alias_args[0]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type_name="tuple",
                            _schema_class=tuple,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                        )
                    )
                elif type_alias_origin is dict:
                    if len(type_alias_args) != 2 or type_alias_args[0] is not str:
                        raise RuntimeError(
                            f"Dict type hint '{cls._serialize_type_alias(type_alias)}'\n"
                            f"for field {field_name} in {TypeUtil.name(containing_type)} is not supported\n"
                            f"because it is not a dictionary with string keys using the syntax 'Dict[str, type]'\n"
                        )
                    type_alias = type_alias_args[1]
                    type_hint_tokens.append(
                        TypeHint(
                            schema_type_name="dict",
                            _schema_class=dict,
                            optional=type_alias_optional,
                            condition=type_alias_condition,
                        )
                    )
                else:
                    supported_container_names = ", ".join([TypeUtil.name(x) for x in supported_containers])
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
                        schema_type_name = TypeUtil.name(type_alias)
                        if field_subtype is None or field_subtype == schema_type_name:
                            type_hint_tokens.append(
                                TypeHint(
                                    schema_type_name=schema_type_name,
                                    _schema_class=type_alias,
                                    optional=type_alias_optional,
                                    condition=type_alias_condition,
                                )
                            )
                        elif field_subtype == "long":
                            if schema_type_name == "int":
                                type_hint_tokens.append(
                                    TypeHint(
                                        schema_type_name="long",
                                        _schema_class=int,
                                        optional=type_alias_optional,
                                        condition=type_alias_condition,
                                    )
                                )
                            else:
                                raise RuntimeError(f"Subtype 'long' is not valid for type hint {type_alias}")
                        elif field_subtype == "timestamp":
                            if schema_type_name == "UUID":
                                type_hint_tokens.append(
                                    TypeHint(
                                        schema_type_name="timestamp",
                                        _schema_class=UUID,
                                        optional=type_alias_optional,
                                        condition=type_alias_condition,
                                    )
                                )
                            else:
                                raise RuntimeError(f"Subtype 'timestamp' is not valid for type hint {type_alias}")
                        else:
                            raise RuntimeError(f"Type name {field_subtype} is not valid for class {schema_type_name}.")
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
    def _link_type_hint_tokens(cls, type_hints: List[Self] | None) -> Self | None:
        """Convert a list of type chain tokens into a linked type chain using the 'remaining' field."""
        if type_hints:
            head, *tail = type_hints
            return TypeHint(
                schema_type_name=head.schema_type_name,
                _schema_class=head._schema_class,
                optional=head.optional,
                condition=head.condition,
                remaining=cls._link_type_hint_tokens(tail),
            )
        else:
            return None
