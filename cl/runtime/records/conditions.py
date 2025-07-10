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
from cl.runtime.records.protocols import TObj, is_sequence, is_primitive
from cl.runtime.records.type_util import TypeUtil


class Condition(Generic[TObj], BootstrapMixin, ABC):
    """Common base class of all query conditions."""

class Range(Generic[TObj], Condition[TObj]):
    """Range with one or two bounds."""

    __slots__ = ("gt_op", "gte_op", "lt_op", "lte_op",)

    gt_op: TObj
    """Value for greater-than operator."""

    gte_op: TObj
    """Value for greater-than-or-equal operator."""

    lt_op: TObj
    """Value for less-than operator."""

    lte_op: TObj
    """Value for less-than-or-equal operator."""

    def __init__(
            self,
            *,
            gt: TObj | None = None,
            gte: TObj | None = None,
            lt: TObj | None = None,
            lte: TObj | None = None,
    ):
        """Create from the individual conditions"""
        self.gt_op = gt
        self.gte_op = gte
        self.lt_op = lt
        self.lte_op = lte


class And(Generic[TObj], Condition[TObj]):
    """Matches when all of the conditions match."""

    __slots__ = ("and_op",)

    and_op: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in And operator."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        self.and_op = tuple(args)


class Or(Generic[TObj], Condition[TObj]):
    """Matches when at least one of the conditions matches."""

    __slots__ = ("or_op",)

    or_op: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in Or operator."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        self.or_op = tuple(args)


class Not(Generic[TObj], Condition[TObj]):
    """Matches when the argument does not match and vice versa."""

    __slots__ = ("not_op",)

    not_op: Condition[TObj] | TObj
    """Applies Not operator to the value."""

    def __init__(self, value: Condition | TObj):
        """Matches when the argument does not match and vice versa."""
        self.not_op = value


class Exists(Generic[TObj], Condition[TObj]):
    """Matches not None if true, matches None if false."""

    __slots__ = ("exists_op",)

    exists_op: bool
    """Matches non-empty value if true, matches empty value if false."""

    def __init__(self, value: bool):
        """Matches non-empty value if true, matches empty value if false."""
        if type(value) is bool:
            self.exists_op = value
        else:
            raise RuntimeError(
                f"Argument of Exists operator has type {TypeUtil.name(value)} which is not a bool.")


class In(Generic[TObj], Condition[TObj]):
    """Matches when the argument is equal to one of the values."""

    __slots__ = ("in_op",)

    in_op: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to use with the In operator."""
        if isinstance(values, tuple):
            self.in_op = values
        elif is_sequence(values):
            self.in_op = tuple(values)
        else:
            raise RuntimeError(
                f"Argument of In operator has type {TypeUtil.name(values)} which is not a sequence.")


class NotIn(Generic[TObj], Condition[TObj]):
    """Matches when the argument is not equal to any of the values."""

    __slots__ = ("nin_op",)

    nin_op: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to use with the NotIn operator."""
        if isinstance(values, tuple):
            self.nin_op = values
        elif is_sequence(values):
            self.nin_op = tuple(values)
        else:
            raise RuntimeError(
                f"Argument of NotIn operator has type {TypeUtil.name(values)} which is not a sequence.")
