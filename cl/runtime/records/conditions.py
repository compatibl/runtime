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
from dataclasses import dataclass
from typing import Generic
from typing import Sequence
from typing import Tuple
from cl.runtime.records.for_dataclasses.data import Data
from cl.runtime.records.protocols import TObj


@dataclass(slots=True)
class Condition(Data, Generic[TObj], ABC):
    """Common base class to query conditions."""


@dataclass(slots=True, init=False)
class And(Condition[TObj], Generic[TObj]):
    """Matches when all of the conditions match."""

    conditions: Tuple[Condition[TObj], ...]
    """The sequence of conditions to match"""

    def __init__(self, *args: Condition[TObj]):
        """Create from the sequence of conditions to match."""
        self.conditions = tuple(args)


@dataclass(slots=True, init=False)
class Or(Condition[TObj], Generic[TObj]):
    """Matches when at least one of the conditions matches."""

    conditions: Tuple[Condition[TObj], ...]
    """The sequence of conditions to match"""

    def __init__(self, *args: Condition[TObj]):
        """Create from the sequence of conditions to match."""
        self.conditions = tuple(args)


@dataclass(slots=True, init=False)
class Not(Condition[TObj], Generic[TObj]):
    """Matches when the argument does not match and vice versa."""

    condition: Condition[TObj]
    """Matches when the argument does not match and vice versa."""

    def __init__(self, condition: Condition):
        """Matches when the argument does not match and vice versa."""
        self.condition = condition


@dataclass(slots=True, init=False)
class Exists(Condition[TObj], Generic[TObj]):
    """Matches not None if True, matches None if false."""

    value: bool
    """Matches not None if True, matches None if false."""

    def __init__(self, value: bool):
        """Matches not None if True, matches None if false."""
        self.value = value


@dataclass(slots=True, init=False)
class Eq(Condition[TObj], Generic[TObj]):
    """Matches when the argument is equal to the value."""

    value: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value to compare to."""
        self.value = value


@dataclass(slots=True, init=False)
class In(Condition[TObj], Generic[TObj]):
    """Matches when the argument is equal to one of the values."""

    values: Tuple[TObj, ...]
    """Sequence of values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to compare to."""
        self.values = values if isinstance(values, tuple) else tuple(values)
