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
from typing_extensions import Self
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.slots_util import SlotsUtil


class KeyMixin(DataMixin, ABC):
    """Mixin class for a key."""

    __slots__ = SlotsUtil.merge_slots(DataMixin)
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    @abstractmethod
    def get_key_type(cls) -> type[Self]:
        """Return key type even when called from a record."""

    def get_table(self) -> str:
        """DB table in PascalCase format (defaults to key type name with Key suffix removed)."""
        return TypeUtil.name(self.get_key_type())
