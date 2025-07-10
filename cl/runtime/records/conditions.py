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

    __slots__ = ("op_gt", "op_gte", "op_lt", "op_lte",)

    op_gt: TObj
    """Value for greater-than operator."""

    op_gte: TObj
    """Value for greater-than-or-equal operator."""

    op_lt: TObj
    """Value for less-than operator."""

    op_lte: TObj
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
        self.op_gt = gt
        self.op_gte = gte
        self.op_lt = lt
        self.op_lte = lte


class Gt(Generic[TObj], Condition[TObj]):
    """Matches when the argument is greater than the value."""

    __slots__ = ("op_gt",)

    op_gt: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value to use with the greater-than operator."""
        if is_primitive(value):
            self.op_gt = value
        else:
            raise RuntimeError(
                f"Argument of Gt operator has type {TypeUtil.name(value)} which is not a primitive.")


class Gte(Generic[TObj], Condition[TObj]):
    """Matches when the argument is greater than or equal to the value."""

    __slots__ = ("op_gte",)

    op_gte: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value to use with the greater-than-or-equal operator."""
        if is_primitive(value):
            self.op_gte = value
        else:
            raise RuntimeError(
                f"Argument of Gte operator has type {TypeUtil.name(value)} which is not a primitive.")


class Lt(Generic[TObj], Condition[TObj]):
    """Matches when the argument is less than the value."""

    __slots__ = ("op_lt",)

    op_lt: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value to use with the less-than operator."""
        if is_primitive(value):
            self.op_lt = value
        else:
            raise RuntimeError(
                f"Argument of Lt operator has type {TypeUtil.name(value)} which is not a primitive.")


class Lte(Generic[TObj], Condition[TObj]):
    """Matches when the argument is less than or equal to the value."""

    __slots__ = ("op_lte",)

    op_lte: TObj
    """Value to compare to."""

    def __init__(self, value: TObj):
        """Create from the value to use with the less-than-or-equal operator."""
        if is_primitive(value):
            self.op_lte = value
        else:
            raise RuntimeError(
                f"Argument of Lte operator has type {TypeUtil.name(value)} which is not a primitive.")


class And(Generic[TObj], Condition[TObj]):
    """Matches when all of the conditions match."""

    __slots__ = ("op_and",)

    op_and: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in And operator."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        self.op_and = tuple(args)


class Or(Generic[TObj], Condition[TObj]):
    """Matches when at least one of the conditions matches."""

    __slots__ = ("op_or",)

    op_or: Tuple[Condition[TObj] | TObj, ...]
    """The sequence of conditions or values in Or operator."""

    def __init__(self, *args: Condition[TObj] | TObj):
        """Create from the sequence of conditions to match."""
        self.op_or = tuple(args)


class Not(Generic[TObj], Condition[TObj]):
    """Matches when the argument does not match and vice versa."""

    __slots__ = ("op_not",)

    op_not: Condition[TObj] | TObj
    """Applies Not operator to the value."""

    def __init__(self, value: Condition | TObj):
        """Matches when the argument does not match and vice versa."""
        self.op_not = value


class Exists(Generic[TObj], Condition[TObj]):
    """Matches not None if true, matches None if false."""

    __slots__ = ("op_exists",)

    op_exists: bool
    """Matches non-empty value if true, matches empty value if false."""

    def __init__(self, value: bool):
        """Matches non-empty value if true, matches empty value if false."""
        if type(value) is bool:
            self.op_exists = value
        else:
            raise RuntimeError(
                f"Argument of Exists operator has type {TypeUtil.name(value)} which is not a bool.")


class In(Generic[TObj], Condition[TObj]):
    """Matches when the argument is equal to one of the values."""

    __slots__ = ("op_in",)

    op_in: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to use with the In operator."""
        if isinstance(values, tuple):
            self.op_in = values
        elif is_sequence(values):
            self.op_in = tuple(values)
        else:
            raise RuntimeError(
                f"Argument of In operator has type {TypeUtil.name(values)} which is not a sequence.")


class NotIn(Generic[TObj], Condition[TObj]):
    """Matches when the argument is not equal to any of the values."""

    __slots__ = ("op_nin",)

    op_nin: Tuple[TObj, ...]
    """Values to compare to."""

    def __init__(self, values: Sequence[TObj]):
        """Create from the sequence of values to use with the NotIn operator."""
        if isinstance(values, tuple):
            self.op_nin = values
        elif is_sequence(values):
            self.op_nin = tuple(values)
        else:
            raise RuntimeError(
                f"Argument of NotIn operator has type {TypeUtil.name(values)} which is not a sequence.")
