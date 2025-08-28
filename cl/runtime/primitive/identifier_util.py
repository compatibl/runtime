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

import unicodedata
from typing import Any
from typing import Collection
from typing import TypeGuard
from cl.runtime.records.typename import typename

_UNICODE_CATEGORY_PREFIXES = {"L", "N"}
"""Allowed Unicode category prefixes."""

_DEFAULT_IDENTIFIER_DELIMITERS = frozenset({" ", "-", "_", "."})
"""Default identifier delimiters when not specified."""

_DIRECTORY_SEPARATORS = frozenset(list(_DEFAULT_IDENTIFIER_DELIMITERS) + [":", "\\", "/"])
"""Directory separators."""

_BRACES = frozenset(list(_DEFAULT_IDENTIFIER_DELIMITERS) + ["{", "}"])
"""Braces for formatted strings."""


class IdentifierUtil:
    """Utilities for working with Unicode identifiers."""

    @classmethod
    def guard_valid_identifier(
        cls,
        value: Any,
        *,
        identifier_delimiters: Collection[str] = _DEFAULT_IDENTIFIER_DELIMITERS,
        allow_directory_separators: bool = False,
        allow_braces: bool = False,
        raise_on_fail: bool = True,
    ) -> TypeGuard[str]:
        """
        Returns true if the string contains only Unicode characters, numbers, or the specified delimiters.

        Args:
            value: The identifier to validate
            identifier_delimiters: The list of allowed delimiters
            allow_directory_separators: Add directory separators to allowed delimiters
            allow_braces: Add braces {} to allowed delimiters
            raise_on_fail: If the validation fails, return None or raise an error depending on raise_on_fail
        """
        if not isinstance(value, str):
            if raise_on_fail:
                raise RuntimeError(f"Identifier '{typename(value)}' type is not string.")
            else:
                return False

        # Expand the set of delimiters based on the specified options
        delimiters = list(identifier_delimiters)
        if allow_directory_separators:
            delimiters.extend(_DIRECTORY_SEPARATORS)
        if allow_braces:
            delimiters.extend(_BRACES)
        delimiters = frozenset(delimiters)

        for pos, char in enumerate(value):
            # Get two-letter Unicode category, e.g., Lu = uppercase letter or Nd = decimal digit,
            # and check that the first letter matches L = Letter or N = Number
            if (category := unicodedata.category(char))[0] in _UNICODE_CATEGORY_PREFIXES:
                # Continue if allowed category
                continue
            elif char in delimiters:
                # Continue if allowed delimiter
                continue
            elif raise_on_fail:
                allowed_categories_str = ", ".join(_UNICODE_CATEGORY_PREFIXES)
                allowed_delimiters_str = ", ".join(delimiters)
                raise RuntimeError(
                    f"Character '{char}' at position {pos} in identifier '{value}' has Unicode category {category}\n"
                    f"which does not have one of the allowed Unicode category prefixes: {allowed_categories_str}\n"
                    f"and it is also not not one of the allowed delimiters: {allowed_delimiters_str}"
                )
            else:
                return False

        # Passed validation if the loop completed
        return True
