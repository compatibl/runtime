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

from typing import Any, Sequence, Tuple
from typing import Dict
from typing import Type
from typing import TypeGuard
from cl.runtime.records.protocols import TObj


class TypeUtil:
    """Helper class for type checking."""

    # TODO: Cache output (convert to use type only, not instance). Consider eliminating instance_or_type.
    @classmethod
    def name(cls, instance_or_type: Any) -> str:
        """Returns TypeAlias.alias if specified and type.name otherwise."""
        type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        result = cls._get_alias_dict().get(type_, type_.__name__)
        return result

    @classmethod
    def check_type(
        cls,
        instance_or_type: Any,
        expected_type: Type[TObj],
        *,
        name: str | None = None,
    ) -> TypeGuard[TObj]:
        """
        Raises an error if the type of 'instance_or_type' is not 'expected_type', subclasses are not permitted.

        Notes:
            Use 'check_subtype' method to allow subclasses to pass the check.

        Args:
            instance_or_type: Actual object or type
            expected_type: Expected type
            name: Lowercase name of parameter or field (optional)
        """
        # If not a type, assume it is an instance
        actual_type = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        if not (actual_type is expected_type):
            # Use default description if the name is not provided
            what = f"The value for {name}" if name else "Parameter or field"
            actual = actual_type.__name__
            expected = expected_type.__name__
            raise RuntimeError(f"{what} has type {actual} where {expected} is expected (subclasses are not permitted).")
        else:
            # Return True if the check passes to use as TypeGuard
            return True

    @classmethod
    def check_subtype(
        cls,
        instance_or_type: Any,
        expected_type: Type[TObj],
        *,
        name: str | None = None,
    ) -> TypeGuard[TObj]:
        """
        Raises an error if the type of 'instance_or_type' is not the same type or subclass of 'expected_type'.

        Args:
            instance_or_type: Actual object or type
            expected_type: Expected type
            name: Lowercase name of parameter or field (optional)
        """
        # If not a type, assume it is an instance
        actual_type = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        if not issubclass(actual_type, expected_type):
            # Use default description if the name is not provided
            what = f"The value for {name}" if name else "Parameter or field"
            actual = actual_type.__name__
            expected = expected_type.__name__
            raise RuntimeError(f"{what} has type {actual} where {expected} or its a subclass is expected.")
        else:
            # Return True if the check passes to use as TypeGuard
            return True

    @classmethod  # TODO: Move to a separate helper class
    def unpack_type_chain(
        cls,
        type_chain: Tuple[str, ...] | None,
    ) -> Tuple[str | None, bool | None, Tuple[str, ...] | None]:
        """
        Parse type chain to return type name, is_optional flag, and remaining chain (if any).

        Returns:
            Tuple of type_name, is_optional flag, and remaining chain (each item can be None)
            Returns [None, None, None] if the type chain is empty or None
        """

        if type_chain is None:
            # Type chain is None
            return None, None, None
        elif not isinstance(type_chain, (list, tuple)):
            raise RuntimeError(f"Type chain {type_chain} for {cls.__name__} is not a list or tuple.")
        elif len(type_chain) == 0:
            raise RuntimeError(f"Type chain {type_chain} for {cls.__name__} has zero length.")
        else:
            # At least one item in type chain is present
            type_hint = type_chain[0]
            remaining_chain = type_chain[1:] if len(type_chain) > 1 else None

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

            return type_name, is_optional, remaining_chain

    @classmethod
    def _get_alias_dict(cls) -> Dict[Type, str]:
        """Get or create a dict of type aliases."""
        # TODO: Implement type aliases
        return {}
