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
from typing import Mapping
from typing import Tuple
from typing import TypeVar
from typing import get_args
from typing import get_origin
from cl.runtime.records.type_util import TypeUtil

_HAS_GET_ORIGINAL_BASES = sys.version_info >= (3, 12)
"""Use types.get_original_bases(cls) for Python 3.12+ and cls.__orig_bases__ for earlier versions."""


class GenericUtil:
    """Helper methods for generic classes."""

    @classmethod
    def is_generic(cls, type_: type) -> bool:
        """Return true if the argument is a generic type."""
        return hasattr(type_, "__parameters__")

    @classmethod
    def get_generic_args(cls, type_, generic_base: type) -> Mapping[str, type]:
        """Return generic argument types passed to the specified generic_base of type_, error if not found."""

        if not cls.is_generic(generic_base):
            raise RuntimeError(
                f"Argument generic_base={TypeUtil.name(generic_base)} of GenericUtil.get_generic_args is not generic."
            )

        if (result := cls._get_generic_args_recursive(type_, generic_base, {})) is not None:
            # Return if found
            return result
        else:
            # Raise an error if not found
            raise RuntimeError(
                f"Generic class {TypeUtil.name(generic_base)} is not a base class of {TypeUtil.name(type_)}"
            )

    @classmethod
    def _get_generic_args_recursive(
        cls,
        type_: type,
        generic_base: type,
        arg_map: dict[TypeVar, type],
    ) -> Mapping[str, type] | None:
        """
        Return generic argument types passed to the specified generic_base of type_, or None if not found.
        Accumulates the intermediate results in arg_map.
        """

        for base in cls._get_original_bases(type_):
            origin = get_origin(base) or base  # Works for both generic and non-generic types
            args = get_args(base)

            # Extend the substitution map with bindings visible at this level
            if args and hasattr(origin, "__parameters__"):
                params = origin.__parameters__
                new_map = arg_map.copy()
                for param, arg in zip(params, args):
                    # If the arg is still a TypeVar, try to resolve via the map
                    if isinstance(arg, TypeVar):
                        arg = arg_map.get(arg, arg)
                    new_map[param] = arg
            else:
                new_map = arg_map

            # If we have reached the target, resolve its parameters and return
            if origin is generic_base:
                return {p.__name__: new_map.get(p, p) for p in generic_base.__parameters__}  # noqa

            # Otherwise, keep searching the hierarchy
            resolved = cls._get_generic_args_recursive(origin, generic_base, new_map)
            if resolved is not None:
                return resolved

        return None  # Not found along this branch

    @classmethod
    def _get_original_bases(cls, type_: type) -> Tuple[type, ...]:
        """Return bases with generic type arguments passed at runtime."""
        if _HAS_GET_ORIGINAL_BASES:
            # Python >= 3.12
            return types.get_original_bases(type_)
        else:
            # Python < 3.12 fallback
            return getattr(type_, "__orig_bases__", ()) or getattr(type_, "__bases__", ())
