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

from abc import abstractmethod
from typing import Generic

from cl.runtime import TypeInfoCache
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import TKey
from cl.runtime.records.type_util import TypeUtil


class RecordMixin(Generic[TKey]):
    """
    Optional generic mixin for a record parameterized by its key.
    Derive MyRecord from MyRecord(MyKey, RecordMixin[MyKey]).
    """

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @abstractmethod
    def get_key(self) -> KeyMixin:
        """Return a new key object whose fields populated from self, do not return self."""
        if hasattr(self, 'serialize_key'):
            serialized_key = self.serialize_key()
            key_type = serialized_key[0]
            remaining_fields = serialized_key[1:]
            result = key_type(*remaining_fields)
            return result
        else:
            raise RuntimeError(f"Type {TypeUtil.name(self)} must implement either get_key or serialize_key method.")
