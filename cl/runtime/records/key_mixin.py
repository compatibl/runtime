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
from typing import Self
from typing import TypeVar
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.typename import typename


class KeyMixin(DataMixin, ABC):
    """Mixin class for a key."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    def get_key_type(cls) -> type[Self]:
        """Return key type even when called from a record."""

    def __hash__(self) -> int:
        """
        Return hash of the key based on its field values.
        Only hashable after the key is frozen via build().
        """
        if not self.is_frozen():
            raise RuntimeError(
                f"Cannot hash an instance of {typename(type(self))} because it is not frozen. "
                f"Invoke build() method before using as a dictionary key or in a set."
            )
        # Invoke hash for each field to call hash recursively for the inner key fields of composite keys
        return hash(tuple(hash(getattr(self, field_name)) for field_name in self.get_field_names()))

    def __eq__(self, other: object) -> bool:  # TODO (Roman): Confirm the need for custom __eq__
        """
        Compare keys for equality based on their type and field values.
        """
        if not isinstance(other, KeyMixin):
            return False
        if type(self) is not type(other):
            return False
        # Compare all field values
        return all(getattr(self, field_name) == getattr(other, field_name) for field_name in self.get_field_names())


TKey = TypeVar("TKey", bound=KeyMixin)
"""Generic type parameter for a key."""
