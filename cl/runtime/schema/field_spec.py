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
from typing import Type
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.for_dataclasses.freezable import Freezable
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.container_decl import ContainerDecl
from cl.runtime.schema.container_kind_enum import ContainerKindEnum


@dataclass(slots=True, kw_only=True)
class FieldSpec(Freezable):
    """Provides information about a field in DataSpec."""

    field_name: str = required()
    """Field name (must be unique within the class)."""
    
    type_name: str = required()
    """Type name (class name or alias, do not include container and optional settings here)."""

    container: ContainerDecl | None = None
    """Container spec if the value is inside a container or multiple nested containers."""

    optional: bool | None = None
    """Indicates if the field can be None (applies to the entire field, not to items inside the container)."""

    _class: Type
    """Class where field type is stored (this is not the type hint as it excludes container and optional info)."""

    def get_class(self) -> Type:
        """Class where the type is stored."""
        return self._class

    @classmethod
    def create(
        cls,
        *,
        type_hint: Type,
        field_name: str,
        containing_type_name: str,
    ) -> Self:
        """
        Create type spec by parsing the type hint.

        Args:
            type_hint: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_name: Name of the field, used for error messages only and recorded into the output
            containing_type_name: Name of the class that contains the field, used for error messages only
                                  and recorded into the output
        """

        # Variables to store the result of type hint parsing
        root_container = None
        root_optional = None

        # Get origin and args of the field type
        type_hint_origin = typing.get_origin(type_hint)
        type_hint_args = typing.get_args(type_hint)

        # There are two possible forms of origin for optional, typing.Union and types.UnionType
        if type_hint_origin is typing.Union or type_hint_origin is types.UnionType:
            # Union with None is the only permitted Union type
            if len(type_hint_args) != 2 or type_hint_args[1] is not type(None):
                raise RuntimeError(
                    f"Union type hint '{type_hint}' for field '{field_name}'\n"
                    f"in record '{containing_type_name}' is not supported\n"
                    f"because it is not an optional value using the syntax 'Type | None'\n"
                )

            # Set optional flag in result
            root_optional = True

            # Get type information without None
            type_hint = type_hint_args[0]
            type_hint_origin = typing.get_origin(type_hint)
            type_hint_args = typing.get_args(type_hint)

        # Check for one of the supported container types
        outer_container = None
        supported_containers = [list, tuple, dict]
        while type_hint_origin in supported_containers:
            if type_hint_origin is list:
                # Perform additional checks for list
                if len(type_hint_args) != 1:
                    raise RuntimeError(
                        f"List type hint '{type_hint}' for field '{field_name}'\n"
                        f"in record '{containing_type_name}' is not supported\n"
                        f"because it is not a list of elements using the syntax 'List[Type]'\n"
                    )
                # Populate container data and extract the inner type_hint
                container = ContainerDecl(container_kind=ContainerKindEnum.LIST)
                type_hint = type_hint_args[0]
            elif type_hint_origin is tuple:
                # Perform additional checks for tuple
                if len(type_hint_args) != 2 or type_hint_args[1] is not Ellipsis:
                    raise RuntimeError(
                        f"Tuple type hint '{type_hint}' for field '{field_name}'\n"
                        f"in record '{containing_type_name}' is not supported\n"
                        f"because it is not a variable-length tuple using the syntax 'Tuple[Type, ...]'\n"
                    )
                # Populate container data and extract the inner type_hint
                container = ContainerDecl(container_kind=ContainerKindEnum.LIST)
                type_hint = type_hint_args[0]
            elif type_hint_origin is dict:
                # Perform additional checks for dict
                if len(type_hint_args) != 2 or type_hint_args[0] is not str:
                    raise RuntimeError(
                        f"Dict type hint '{type_hint}' for field '{field_name}'\n"
                        f"in record '{containing_type_name}' is not supported\n"
                        f"because it is not a dictionary with string keys using the syntax 'Dict[str, Type]'\n"
                    )
                # Populate container data and extract the inner type_hint
                container = ContainerDecl(container_kind=ContainerKindEnum.DICT)
                type_hint = type_hint_args[1]
            else:
                supported_container_names = ", ".join([TypeUtil.name(x) for x in supported_containers])
                raise RuntimeError(
                    f"Type {type_hint_origin.__name__} is not one of the supported container types "
                    f"{supported_container_names}."
                )

            # Strip container information from type_hint to get the type of value inside the container
            type_hint_origin = typing.get_origin(type_hint)
            type_hint_args = typing.get_args(type_hint)

            # There are two possible forms of origin for optional, typing.Union and types.UnionType
            if type_hint_origin is typing.Union or type_hint_origin is types.UnionType:
                # Union with None is the only permitted Union type
                if len(type_hint_args) != 2 or type_hint_args[1] is not type(None):
                    raise RuntimeError(
                        f"Union type hint '{type_hint}' for an element of\n"
                        f"the {container.container_kind.name}field '{field_name}'\n"
                        f"in record '{containing_type_name}' is not supported\n"
                        f"because it is not an optional value using the syntax 'Type | None'\n"
                    )

                # Indicate that container elements can be None
                container.optional_items = True

                # Get type information without None
                type_hint = type_hint_args[0]
                type_hint_origin = typing.get_origin(type_hint)
                type_hint_args = typing.get_args(type_hint)  # TODO: Add a check

            # Assign container to result or outer container
            if outer_container is None:
                root_container = container
            else:
                outer_container.inner = container
            outer_container = container

        # Check that type hint is completely unwrapped and only the
        # genuine inner type remains without wrappers from typing
        if type_hint_origin is None and not type_hint_args and isinstance(type_hint, type):
            # Create the field spec and return
            result = cls(
                field_name=field_name,
                type_name=TypeUtil.name(type_hint),
                container=root_container,
                optional=root_optional,
                _class=type_hint
            )
            return result
        else:
            raise RuntimeError(f"Type hint format {type_hint} is not recognized.")
