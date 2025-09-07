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
        # TODO: Add support for aliases
        return type_.__name__
    else:
        raise RuntimeError(
            f"Function typename accepts only type but an instance of {typename(type(type_))} was provided instead."
        )


def typenameof(value: Any) -> str:
    """Shortcut for typename(typeof(value))."""
    return typename(typeof(value))
