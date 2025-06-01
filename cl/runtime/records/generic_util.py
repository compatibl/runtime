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
from frozendict import frozendict
from memoization import cached
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
    @cached
    def is_generic(cls, type_: type) -> bool:
        """Return true if the argument is a generic type."""
        return hasattr(type_, "__parameters__")

    @classmethod
    @cached
    def get_concrete_type(cls, type_: type, type_var: TypeVar) -> type:
        """Get concrete type for the specified generic type and TypeVar in its inheritance hierarchy."""
        concrete_type_dict = cls.get_concrete_type_dict(type_)
        if (result := concrete_type_dict.get(type_var.__name__, None)) is not None:
            return result
        else:
            raise RuntimeError(f"Type {TypeUtil.name(type_)} and its ancestors have "
                               f"no generic parameter (TypeVar) with name {type_var.__name__}.")

    @classmethod
    @cached
    def get_concrete_type_dict(cls, type_: type) -> Mapping[str, type]:
        """Walk the inheritance tree of type_ and return a mapping of TypeVar name to concrete_type."""
        result = cls._collect_generic_args_recursive(type_)
        return frozendict(result)

    @classmethod
    def _collect_generic_args_recursive(          # ← new name, no generic_base
        cls,
        type_: type,
        *,
        arg_map: dict[TypeVar, type] | None = None,
        seen_types: set[type] | None = None,
    ) -> Mapping[str, type]:
        """
        Recursive helper to walk the inheritance tree of type_ and return a mapping of TypeVar name to concrete_type.

        Args:
            type_: The type to inspect
            arg_map: The mapping where results are collected, use for recursion only
            seen_types: Protect against diamonds in inheritance graph, use for recursion only

        Notes:
            Error message if the same TypeVar name occurs more than once.
        """
        if arg_map is None:
            arg_map = {}
        if seen_types is None:
            seen_types = set()
        if type_ in seen_types:
            return {}

        seen_types.add(type_)
        result: dict[str, type] = {}

        for base in cls._get_original_bases(type_):
            origin = get_origin(base) or base
            args = get_args(base)

            # Build a substitution map visible at this level
            if args and hasattr(origin, "__parameters__"):
                params = origin.__parameters__
                level_map = arg_map.copy()
                for param, arg in zip(params, args):
                    if isinstance(arg, TypeVar):
                        arg = arg_map.get(arg, arg)
                    level_map[param] = arg
            else:
                level_map = arg_map

            # Record resolved parameters for origin
            if hasattr(origin, "__parameters__"):
                for p in origin.__parameters__:
                    resolved = level_map.get(p, p)
                    name = p.__name__
                    # Error message if the same name refers to different things
                    if name in result and result[name] is not resolved:
                        raise RuntimeError(
                            "Not all TypeVar names are unique across "
                            "the class hierarchy (duplicate {!r})".format(name)
                        )
                    result[name] = resolved

            # Call recursively for ancestor types
            sub = cls._collect_generic_args_recursive(origin, arg_map=level_map, seen_types=seen_types)
            for name, resolved in sub.items():
                if name in result and result[name] is not resolved:
                    raise RuntimeError(
                        "Not all TypeVar names are unique across "
                        "the class hierarchy (duplicate {!r})".format(name)
                    )
                result.setdefault(name, resolved)

        return result


    @classmethod
    def _get_original_bases(cls, type_: type) -> Tuple[type, ...]:
        """Return bases with generic type arguments passed at runtime."""
        if _HAS_GET_ORIGINAL_BASES:
            # Python >= 3.12
            return types.get_original_bases(type_)
        else:
            # Python < 3.12 fallback
            return getattr(type_, "__orig_bases__", ()) or getattr(type_, "__bases__", ())
