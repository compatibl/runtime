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

from abc import ABC
from typing import Generic
from typing import Sequence
from typing import Tuple
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.protocols import TObj


class Condition(Generic[TObj], BootstrapMixin, ABC):
    """Common base class of all query conditions."""


class Eq(Generic[TObj], Condition[TObj]):
    """Matches when the argument is equal to the value, equivalent to specifying the value itself."""

    __slots__ = ("value",)

    value: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value."""
        object.__setattr__(self, "value", value)


class And(Generic[TObj], Condition[TObj]):
    """Matches when all of the conditions match."""

    __slots__ = ("conditions",)

    conditions: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in AND."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        object.__setattr__(self, "conditions", tuple(args))


class Or(Generic[TObj], Condition[TObj]):
    """Matches when at least one of the conditions matches."""

    __slots__ = ("conditions",)

    conditions: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in OR."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        object.__setattr__(self, "conditions", tuple(args))


class Not(Generic[TObj], Condition[TObj]):
    """Matches when the argument does not match and vice versa."""

    __slots__ = ("condition",)

    condition: Condition[TObj] | TObj
    """Applies OR operator to the argument."""

    def __init__(self, condition: Condition | TObj):
        """Matches when the argument does not match and vice versa."""
        object.__setattr__(self, "condition", condition)


class Exists(Generic[TObj], Condition[TObj]):
    """Matches not None if true, matches None if false."""

    __slots__ = ("value",)

    value: bool
    """Matches non-empty value if true, matches empty value if false."""

    def __init__(self, value: bool):
        """Matches non-empty value if true, matches empty value if false."""
        object.__setattr__(self, "value", value)


class In(Generic[TObj], Condition[TObj]):
    """Matches when the argument is equal to one of the values."""

    __slots__ = ("values",)

    values: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to compare to."""
        if not isinstance(values, tuple):
            object.__setattr__(self, "values", tuple(values))


class NotIn(Generic[TObj], Condition[TObj]):
    """Matches when the argument is not equal to any of the values."""

    __slots__ = ("values",)

    values: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to compare to."""
        if not isinstance(values, tuple):
            object.__setattr__(self, "values", tuple(values))
