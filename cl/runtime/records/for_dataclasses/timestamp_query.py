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

from dataclasses import dataclass
from typing import Sequence, List
from uuid import UUID
from cl.runtime.records.for_dataclasses.primitive_query import PrimitiveQuery


@dataclass(slots=True, kw_only=True)
class TimestampQuery(PrimitiveQuery):
    """Query for a timestamp field."""

    exists: bool | None = None
    """Matches values other than None if exists=True, matches None if exists=False."""

    eq: UUID | None = None
    """Equal."""

    in_: List[UUID] | None = None
    """Equal to at least one item in the sequence."""

    lt: UUID | None = None
    """Less than."""

    lte: UUID | None = None
    """Less than or equal."""

    gt: UUID | None = None
    """Greater than."""

    gte: UUID | None = None
    """Greater than or equal."""
