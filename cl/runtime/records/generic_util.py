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

import sys
import types
from typing import Tuple, get_origin, get_args
from cl.runtime.records.type_util import TypeUtil

_HAS_GET_ORIGINAL_BASES = sys.version_info >= (3, 12)
"""Use types.get_original_bases(cls) for Python 3.12+ and cls.__orig_bases__ for earlier versions."""


class GenericUtil:
    """Helper methods for generic classes."""

    @classmethod
    def get_generic_args(cls, type_, generic_base: type) -> Tuple[type, ...]:
        """Return a tuple of types passed as generic arguments to 'generic_base' of 'type_', error if not found."""

        if not cls.is_generic(generic_base):
            raise RuntimeError(
                f"Argument generic_base={TypeUtil.name(generic_base)} of GenericUtil.get_generic_args is not generic.")

        if (result := cls.get_generic_args_or_none(type_, generic_base)) is not None:
            # Return if found
            return result
        else:
            # Raise the appropriate error if not found
            raise RuntimeError(
                f"Generic class {TypeUtil.name(generic_base)} is not a base class of {TypeUtil.name(type_)}")

    @classmethod
    def get_generic_args_or_none(cls, type_, generic_base: type) -> Tuple[type, ...] | None:
        """Return a tuple of types passed as generic arguments to 'generic_base' of 'type_', None if not found."""

        # Get bases with generic parameter types that can be resolved at runtime
        orig_bases = cls._get_original_bases(type_)

        # Iterate until generic_base is found
        for base in orig_bases:
            if (origin := get_origin(base)) is generic_base:
                # Matched one of immediate bases of type_
                result = get_args(base)
                return result
            elif (result := cls.get_generic_args_or_none(base, generic_base)) is not None:
                # Invoke recursively for the next level ancestors
                return result

        # Return None if not found
        return None

    @classmethod
    def is_generic(cls, type_: type) -> bool:
        """Return true if the argument is a generic type."""
        return hasattr(type_, "__parameters__")

    @classmethod
    def _get_original_bases(cls, type_: type) -> Tuple[type, ...]:
        """Same as types.get_original_bases with backward compatibility to Python 3.10."""

        # Get bases with generic parameter types that can be resolved at runtime
        if _HAS_GET_ORIGINAL_BASES:
            # Use the new API
            return types.get_original_bases(type_)
        else:
            # Use the old API
            try:
                # Has generic bases, return
                return type_.__orig_bases__
            except AttributeError:
                try:
                    # Return __bases__ if __orig_bases__ is not available to match
                    # the behavior of types.get_original_bases(type_)
                    return type_.__bases__
                except AttributeError:
                    return tuple()

