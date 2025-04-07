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

import datetime as dt
import types
import typing
from dataclasses import dataclass
from typing import Type
from uuid import UUID
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import PRIMITIVE_CLASSES
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.container_decl import ContainerDecl
from cl.runtime.schema.container_kind import ContainerKind
from cl.runtime.schema.type_decl_key import TypeDeclKey
from cl.runtime.schema.type_kind import TypeKind

primitive_types = (str, float, bool, int, dt.date, dt.time, dt.datetime, UUID, bytes)
"""Tuple of primitive types."""

primitive_modules = ["builtins", "datetime", "uuid"]
"""List of modules for primitive types."""


@dataclass(slots=True, kw_only=True)
class FieldDecl:
    """Field declaration."""

    name: str = required()
    """Field name."""

    label: str | None = None
    """Field label (if not specified, titleized name is used instead)."""

    comment: str | None = None
    """Field comment."""

    field_kind: TypeKind = required()
    """Kind of the element inside the innermost container if the field is a container, otherwise kind of the field."""

    field_type_decl: TypeDeclKey = required()
    """Declaration for the field type."""

    container: ContainerDecl | None = None
    """Container declaration if the value is inside a container."""

    optional_field: bool = False
    """Indicates if the entire field can be None."""

    additive: bool | None = None
    """Optional flag indicating if the element is additive (i.e., its sum across records has meaning)."""

    formatter: str | None = None
    """Format string used to display the element using Python conventions ."""

    alternate_of: str | None = None
    """This field is an alternate of the specified field, of which only one can be specified."""

    @classmethod
    def create(
        cls,
        record_type: Type,
        field_name: str,
        field_type: Type,
        field_comment: str,
        *,
        dependencies: typing.Set[Type] | None = None,
    ) -> Self:
        """
        Create from field name and type.

        Args:
            record_type: Type of the record for which the field is defined
            field_name: Name of the field
            field_type: Type of the field obtained from get_type_hints where ForwardRefs are resolved
            field_comment: Field comment (docstring), currently requires source parsing due Python limitations
            dependencies: Set of types used in field or methods of the specified type, populated only if not None
        """

        from cl.runtime import TypeImport  # TODO: Avoid circular dependency

        result = cls()
        result.name = field_name
        result.comment = field_comment

        # Get origin and args of the field type
        field_origin = typing.get_origin(field_type)
        field_args = typing.get_args(field_type)

        # There are two possible forms of origin for optional, typing.Union and types.UnionType
        if field_origin is typing.Union or field_origin is types.UnionType:
            # Union with None is the only permitted Union type
            if len(field_args) != 2 or field_args[1] is not type(None):
                raise RuntimeError(
                    f"Union type hint '{field_type}' for field '{field_name}'\n"
                    f"in record '{TypeUtil.name(record_type)}' is not supported for DB schema\n"
                    f"because it is not an optional value using the syntax 'Type | None',\n"
                    f"where None is placed second per the standard convention.\n"
                    f"It cannot be used to specify a choice between two types.\n"
                )

            # Set optional flag in result
            result.optional_field = True

            # Get type information without None
            field_type = field_args[0]
            field_origin = typing.get_origin(field_type)
            field_args = typing.get_args(field_type)
        else:
            # Set optional flag in result
            result.optional_field = False

        # Check for one of the supported container types
        outer_container = None
        supported_containers = [list, tuple, dict]
        while field_origin in supported_containers:
            if field_origin is list:
                container = ContainerDecl(container_kind=ContainerKind.LIST)
                # Perform additional checks for list
                if len(field_args) != 1:
                    raise RuntimeError(
                        f"List type hint '{field_type}' for field '{field_name}'\n"
                        f"in record '{TypeUtil.name(record_type)}' is not supported for DB schema\n"
                        f"because it is not a list of elements using the syntax 'List[Type]'.\n"
                        f"Other list type hint formats are not supported.\n"
                    )
            elif field_origin is tuple:
                container = ContainerDecl(container_kind=ContainerKind.LIST)
                # Perform additional checks for tuple
                if len(field_args) == 1 or (len(field_args) > 1 and field_args[1] is not Ellipsis):
                    raise RuntimeError(
                        f"Tuple type hint '{field_type}' for field '{field_name}'\n"
                        f"in record '{TypeUtil.name(record_type)}' is not supported for DB schema\n"
                        f"because it is not a variable-length tuple using the syntax 'Tuple[Type, ...]',\n"
                        f"where ellipsis '...' is placed second per the standard convention.\n"
                        f"It cannot be used to specify a fixed size tuple or a tuple with\n"
                        f"different element types.\n"
                    )
            elif field_origin is dict:
                container = ContainerDecl(container_kind=ContainerKind.DICT)
                # Perform additional checks for dict
                if len(field_args) != 2 and field_args[0] is not str:
                    raise RuntimeError(
                        f"Dict type hint '{field_type}' for field '{field_name}'\n"
                        f"in record '{TypeUtil.name(record_type)}' is not supported for DB schema\n"
                        f"because it is not a dictionary with string keys using the syntax 'Dict[str, Type]'.\n"
                        f"It cannot be used to specify a dictionary with keys of a different type.\n"
                    )
                # TODO: Support Dict[str, List[x]]
            else:
                supported_container_names = ", ".join([TypeUtil.name(x) for x in supported_containers])
                raise RuntimeError(
                    f"Type {field_origin.__name__} is not one of the supported container types "
                    f"{supported_container_names}."
                )

            # Strip container information from field_type to get the type of value inside the container
            field_type = field_args[0]
            field_origin = typing.get_origin(field_type)
            field_args = typing.get_args(field_type)

            # There are two possible forms of origin for optional, typing.Union and types.UnionType
            if field_origin is typing.Union or field_origin is types.UnionType:
                # Union with None is the only permitted Union type
                if len(field_args) != 2 or field_args[1] is not type(None):
                    raise RuntimeError(
                        f"Union type hint '{field_type}' for an element of\n"
                        f"the {container.container_kind.name}field '{field_name}'\n"
                        f"in record '{TypeUtil.name(record_type)}' is not supported for DB schema\n"
                        f"because it is not an optional value using the syntax 'Type | None',\n"
                        f"where None is placed second per the standard convention.\n"
                        f"It cannot be used to specify a choice between two types.\n"
                    )

                # Indicate that container elements can be None
                container.optional_items = True

                # Get type information without None
                field_type = field_args[0]
                field_origin = typing.get_origin(field_type)
                field_args = typing.get_args(field_type)  # TODO: Add a check

            # Assign container to result or outer container
            if outer_container is None:
                result.container = container
            else:
                outer_container.inner = container
            outer_container = container

        # Parse the value itself
        if field_origin in supported_containers:
            raise RuntimeError("Containers within containers are not supported when building database schema.")
        elif field_origin is None:

            # Assign type declaration key
            result.field_type_decl = TypeDeclKey.from_type(field_type)

            # Add field type to dependencies, do not use if dependencies to prevent from skipping on first item added
            if dependencies is not None and not is_primitive(field_type):
                dependencies.add(field_type)

            # Assign field kind
            if field_type in PRIMITIVE_CLASSES:
                # Field is one of the supported primitive types
                result.field_kind = TypeKind.PRIMITIVE
            elif is_enum(field_type):
                # Field is an enum
                result.field_kind = TypeKind.ENUM
            elif is_key(field_type):
                # Field is a key (excludes records)
                result.field_kind = TypeKind.KEY
            elif is_record(field_type):
                # Field is a record (excludes keys)
                result.field_kind = TypeKind.RECORD
            elif is_data(field_type):
                # Field is a slotted data type (excludes keys and records)
                result.field_kind = TypeKind.DATA
            else:
                raise RuntimeError(
                    f"Field type '{field_type}' for field '{field_name}' is not\n"
                    f"a primitive type, enum, key, record or a slotted data type."
                )
        else:
            raise RuntimeError(f"Complex type {field_type} is not supported when building database schema.")

        return result
