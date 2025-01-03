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

from typing import Any
from typing import Type


class TypeUtil:
    """Helper class for type checking."""

    @classmethod
    def name(cls, instance_or_type: Any) -> str:
        """Returns TypeAlias.alias if specified and type.name otherwise."""
        # TODO: Return type.__name__ for all types until TypeAlias is supported
        type_ = instance_or_type if isinstance(instance_or_type, type) else type(instance_or_type)
        return type_.__name__

    @classmethod
    def check_same_type(
        cls,
        instance_or_type: Any,
        expected_type: Type,
        *,
        name: str | None = None,
    ) -> None:
        """
        Raises an error if the type of 'actual_instance_or_type' is not 'expected_type', subclasses are not permitted.

        Notes:
            Use 'check_subclass' method to allow subclasses to pass the check.

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

    @classmethod
    def check_subclass(
        cls,
        instance_or_type: Any,
        expected_type: Type,
        *,
        name: str | None = None,
    ) -> None:
        """
        Raises an error if the type of 'actual_instance_or_type' is not the same type or subclass of 'expected_type'.

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
