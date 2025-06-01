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
from typing import Any
from typing import Mapping
from typing import Tuple
from typing import TypeVar
from typing import get_args
from typing import get_origin
from frozendict import frozendict
from memoization import cached
from cl.runtime.records.type_util import TypeUtil

_HAS_GET_ORIGINAL_BASES = sys.version_info >= (3, 12)
"""Use types.get_original_bases(cls) for Python 3.12+ and cls.__orig_bases__ for earlier versions."""


class GenericUtil:
    """Helper methods for generic classes."""

    @classmethod
    @cached
    def is_generic_or_subclass(cls, type_: type) -> bool:
        """Return True if the type or its ancestor has generic parameters, even if concrete types were substituted."""
        return hasattr(type_, "__parameters__")

    @classmethod
    def is_instance(cls, obj: Any, type_: type | types.GenericAlias) -> bool:
        """Return True if the object is an instance of type or GenericAlias."""
        if (origin := get_origin(type_)) is not None:  # or isinstance(type_, types.GenericAlias):
            return isinstance(obj, origin)
        elif isinstance(type_, type):
            return isinstance(obj, type_)
        else:
            raise RuntimeError(f"Type parameter {type_} of GenericUtil.is_instance is not a type or GenericAlias.")

    @classmethod
    @cached
    def get_concrete_type(cls, type_: type, type_var: TypeVar) -> type:
        """Get concrete type for the specified generic type and TypeVar in its inheritance hierarchy."""
        concrete_type_dict = cls.get_concrete_type_dict(type_)
        if (result := concrete_type_dict.get(type_var.__name__, None)) is not None:
            return result
        else:
            raise RuntimeError(
                f"Type {TypeUtil.name(type_)} and its ancestors have "
                f"no generic parameter (TypeVar) with name {type_var.__name__}."
            )

    @classmethod
    @cached
    def get_concrete_type_dict(cls, type_: type) -> Mapping[str, type]:
        """
        Walk the inheritance tree of type_ and return a mapping of TypeVar name to concrete_type.
        If a TypeVar remains unresolved after the walk, it is replaced by its 'bound' parameter.
        """

        # Collect concrete types from the inheritance chain
        result = cls._collect_generic_args_recursive(type_)

        # Substitute bound for any TypeVars that remain unresolved
        result = {
            name: (cls._get_required_bound(value) if isinstance(value, TypeVar) else value)
            for name, value in result.items()
        }

        # Also include any TypeVars from the class parameters that were not in the result
        if hasattr(type_, "__parameters__"):
            for param in type_.__parameters__:
                if param.__name__ not in result:
                    result[param.__name__] = cls._get_required_bound(param)

        return frozendict(result)

    @classmethod
    def _collect_generic_args_recursive(
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

        # Handle parameterised generic aliases
        origin = get_origin(type_)
        if origin is not None and hasattr(origin, "__parameters__"):
            params = origin.__parameters__
            args = get_args(type_)

            # build a level-local substitution map
            level_map = arg_map.copy()
            for param, arg in zip(params, args):
                if isinstance(arg, TypeVar):
                    arg = arg_map.get(arg, arg)
                level_map[param] = arg
                # Record the concrete type
                result[param.__name__] = arg

            # keep walking the hierarchy starting from the underlying class
            sub = cls._collect_generic_args_recursive(origin, arg_map=level_map, seen_types=seen_types)
            for name, resolved in sub.items():
                if name in result and result[name] is not resolved:
                    raise RuntimeError(
                        "Not all TypeVar names are unique across " f"the class hierarchy (duplicate {name!r})"
                    )
                result.setdefault(name, resolved)

            return result

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
                        "Not all TypeVar names are unique across " "the class hierarchy (duplicate {!r})".format(name)
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

    @classmethod
    def _get_required_bound(cls, type_var: TypeVar) -> type:
        """Get 'bound' parameter of TypeVar, error message if not specified."""
        if (result := type_var.__bound__) is not None:
            return result
        else:
            raise RuntimeError(
                f"TypeVar {type_var.__name__} does not specify 'bound' parameter.\n"
                f"To be used in generic records, TypeVars must be bound to a key, record, or slotted type."
            )
