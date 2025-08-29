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


class KeyMixin(DataMixin, ABC):
    """Mixin class for a key."""

    __slots__ = ()

    @classmethod
    @abstractmethod
    def get_key_type(cls) -> type[Self]:
        """Return key type even when called from a record."""


TKey = TypeVar("TKey", bound=KeyMixin)
"""Generic type parameter for a key."""
