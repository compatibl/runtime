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

from cl.runtime.serializers.slots_util import SlotsUtil
from cl.runtime.records.for_slotted.data import Data
from cl.runtime.records.key_mixin import KeyMixin


class Key(Data, KeyMixin, ABC):
    """Base class for keys and records (derived from keys) not based on any data class framework."""

    __slots__ = SlotsUtil.merge_slots(Data)

    def __init__(self) -> None:
        """Initialize instance attributes."""
        super().__init__()
