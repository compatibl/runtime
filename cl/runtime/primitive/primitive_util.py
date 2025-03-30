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

from typing import Any, Type
from typing import Tuple
from cl.runtime.records.type_util import TypeUtil


class PrimitiveUtil:
    """Helper methods for primitive types."""

    @classmethod
    def check_type(
        cls,
        instance_or_type: Any,
        schema_type_name: str,
        *,
        name: str | None = None,
    ) -> None:
        """
        Raises an error if the type of 'instance_or_type' is not 'schema_type', subclasses are not permitted.

        Args:
            instance_or_type: Actual object or type
            schema_type_name: Expected primitive type name, may not match class name (e.g., 'long' or 'timestamp')
            name: Lowercase name of parameter or field (optional)
        """
        # If not a type, assume it is an instance
        value_class_name = TypeUtil.name(instance_or_type)

        # Validate that schema_type_name is compatible with value_class_name if specified
        # Because the value of None is passed through, value_class_name NoneType is compatible with any schema_type_name
        if schema_type_name is not None and value_class_name != "NoneType" and schema_type_name != value_class_name:
            if schema_type_name == "long":
                if value_class_name != "int":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using int class, not {value_class_name} class."
                    )
            elif schema_type_name == "timestamp":
                if value_class_name != "UUID":
                    raise RuntimeError(
                        f"Type {schema_type_name} can only be stored using UUID class, not {value_class_name} class."
                    )
            elif value_class_name != schema_type_name:
                raise RuntimeError(f"Type {schema_type_name} cannot be stored as {value_class_name} class.")

    @classmethod  # TODO: Move to a separate helper class
    def unpack_type_chain(cls, type_chain: Tuple[Tuple[str, Type, bool], ...] | None) -> Tuple[str | Type | None, bool | None]:
        """
        Parse type chain to return type name and is_optional flag, check that there is no remaining chain.

        Returns:
            Tuple of type name and is_optional flag, each tuple item can be None
            Returns [None, None] if the type chain is empty or None
        """

        if type_chain is None:
            # Type chain is None
            return None, None
        elif not isinstance(type_chain, (list, tuple)):
            raise RuntimeError(f"Type chain {type_chain} for a primitive type is not a list or tuple.")
        elif len(type_chain) == 1:
            # At least one item in type chain is present
            type_hint = type_chain[0]

            # Parse type hint to get type name and optional flag
            type_tokens = type_chain[0].split("|")
            if len(type_tokens) == 2 and type_tokens[1].strip() == "None":
                type_name = type_tokens[0].strip()
                is_optional = True
            elif len(type_tokens) == 1:
                type_name = type_tokens[0].strip()
                is_optional = None  # Use None to indicate False
            else:
                raise RuntimeError(
                    f"Type hint {type_hint} does not follow the format 'type_name' or 'type_name | None'."
                )

            return type_name, is_optional
        else:
            raise RuntimeError(f"Type chain {type_chain} for primitive type is not a list of size 1.")
