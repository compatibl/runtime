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
from abc import abstractmethod
from typing import Tuple
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.slots_util import SlotsUtil


class KeyMixin(DataMixin, ABC):
    """Mixin class for a key."""

    __slots__ = SlotsUtil.merge_slots(DataMixin)
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    @abstractmethod
    def get_key_type(cls) -> type:
        """Return key type even when called from a record."""

    def get_table(self) -> str:
        """Return table name for this record as a PascalCase string, return key type name by default."""
        return TypeUtil.name(self.get_key_type())

    def serialize_key(self) -> Tuple:
        """Implement using get_key_type during transition to the new API."""
        if hasattr(self, "get_key_type"):
            key_type = self.get_key_type()
            key_slots = SlotsUtil.get_slots(key_type)
            key_fields = tuple(
                v.serialize_key() if is_key(v := getattr(self, key_slot, None)) else v for key_slot in key_slots
            )
            result = (key_type,) + key_fields
            return result
        else:
            raise RuntimeError(
                f"Type {TypeUtil.name(self)} must implement either get_key_type or serialize_key method."
            )
