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
        """The actual types passed as arguments to the generic base class 'generic_base' of 'type_'."""

        # Get bases with generic parameter types that can be resolved at runtime
        orig_bases = cls._get_original_bases(type_)

        # Iterate until generic_base is found
        for base in orig_bases:
            if get_origin(base) is generic_base:
                result = get_args(base)
                return result

        # Error message if not found
        if not hasattr(generic_base, "__parameters__"):
            raise RuntimeError(
                f"Argument generic_base={TypeUtil.name(generic_base)} of GenericUtil.get_generic_args is not generic.")
        else:
            raise RuntimeError(
                f"Generic class {TypeUtil.name(generic_base)} is not a base class of {TypeUtil.name(type_)}")

    @classmethod
    def _get_original_bases(cls, type_: type) -> Tuple[type, ...]:
        """Same as types.get_original_bases with backward compatibility to Python 3.10."""

        # Get bases with generic parameter types that can be resolved at runtime
        if _HAS_GET_ORIGINAL_BASES:
            # Use the new API
            return types.get_original_bases(type_)
        else:
            # Use the old API
            if orig_bases := getattr(type_, "__orig_bases__", None):
                # Has generic bases, return
                return orig_bases
            else:
                # Return __bases__ if __orig_bases__ is not available to match
                # the behavior of types.get_original_bases(type_)
                return type_.__bases__
