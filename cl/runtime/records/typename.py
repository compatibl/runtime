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

from typing import Any, get_origin
from memoization import cached


def typeof(value: Any) -> type:
    """Return type of the specified instance, converting ABCMeta and other metaclasses to type."""
    result = type(value)
    if issubclass(result, type):
        # If the result is a metaclass, convert to plain type
        result = type
    return result


@cached
def typename(type_: type) -> str:
    """
    Return type name without module in PascalCase, or an alias if provided.
    This method accepts type only, error if an if instance is provided.
    """
    if isinstance(type_, type):
        # Non-generic type
        return type_.__name__
    elif (type_origin := get_origin(type_)) is not None:
        # Parametrized generic including _GenericAlias
        return type_origin.__name__
    else:
        raise RuntimeError(
            f"Function typename accepts only type but an instance of {typename(type(type_))} was provided instead."
        )


def typenameof(value: Any) -> str:
    """Shortcut for typename(typeof(value))."""
    return typename(typeof(value))


def qualname(type_: type) -> str:
    """Return fully qualified type name with module in module.PascalCase format without applying any aliases."""
    # Accept type only, error if an instance is passed
    if isinstance(type_, type):
        return f"{type_.__module__}.{type_.__name__}"
    else:
        raise RuntimeError(
            f"Function qualname accepts only type but an instance of {qualname(type(type_))} was provided instead."
        )


def qualnameof(value: Any) -> str:
    """Shortcut for qualname(typeof(value))."""
    return typename(typeof(value))
