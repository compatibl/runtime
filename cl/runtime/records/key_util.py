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

import ast
import inspect
import textwrap
from typing import List
from typing import Sequence
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import KeyProtocol
from cl.runtime.records.type_util import TypeUtil


class KeyUtil:  # TODO: Review how the methods are used
    """Utilities for working with keys."""

    @classmethod
    def format(cls, value: KeyProtocol) -> str:
        """Convert to semicolon-delimited string without type (error message if value is None)."""
        # TODO: Remove, use key_serializer instead
        # TODO: Improve and check usage
        if value is not None:
            return cls.serialize(value)
        else:
            raise RuntimeError("Argument to KeyUtil.format method is None or an empty string.")

    @classmethod
    def serialize(cls, value: KeyProtocol | None) -> str | None:
        """Convert to semicolon-delimited string without type (return None if argument is None)."""
        # TODO: Remove, use key_serializer instead
        return str(value)  # TODO: Add checks

    @classmethod
    def get_key_type(cls, *, table: str, records_or_keys: Sequence[KeyMixin]) -> type[KeyMixin]:
        """Ensure all keys within the table have the same type and return that type, error otherwise."""
        if not records_or_keys:
            raise RuntimeError(f"Param 'records_or_keys' for table {table} in KeyUtil.get_key_type is None or empty.")

        # Create a set of unique keys
        key_types = {key.get_key_type() for key in records_or_keys}
        if len(key_types) == 1:
            return key_types.pop()
        else:
            key_types_str = "\n".join(sorted(TypeUtil.name(key_type) for key_type in key_types))
            raise RuntimeError(f"More than one key type is specified for table {table}:\n{key_types_str}\n")

    # TODO: Extract from key class instead
    @classmethod
    def get_key_fields(cls, record_type: type) -> list[str] | None:
        """
        Get primary key fields by parsing the source of 'get_key' method of 'record_type'.

        Notes:
            This method parses the source code of 'get_key' method of 'record_type' and returns all
            instance fields it accesses in the order of access, for example if 'get_key' source is:

            def get_key(self) -> MyKey:
                return MyKey(key_field_1=self.key_field_1, key_field_2=self.key_field_2).build()

            this method will return:

            ["key_field_1", "key_field_2"]

        Args:
            record_type: Class where 'get_key' method is implemented
        """

        # Get source code for the 'get_key' method
        if hasattr(record_type, "get_key"):
            get_key_source = inspect.getsource(record_type.get_key)
        else:
            # TODO: Determine if a flag is needed for element types to prevent keys lookup
            return None
            # raise RuntimeError(
            #    f"Cannot get key fields because record type {TypeUtil.name(record_type)} "
            #    f"does not implement 'get_key' method."
            # )

        # Because 'ast' expects the code to be correct as though it is at top level,
        # remove excess indent from the source to make it suitable for parsing
        get_key_source = textwrap.dedent(get_key_source)

        # Extract field names from the AST of 'get_key' method
        get_key_ast = ast.parse(get_key_source)
        key_fields = []
        for node in ast.walk(get_key_ast):
            # Find every instance field of accessed inside the source of 'get_key' method.
            # Accumulate in list in the order they are accessed
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
                key_fields.append(node.attr)

        return key_fields
