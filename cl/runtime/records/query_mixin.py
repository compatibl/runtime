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
from cl.runtime.records.partition_mixin import PartitionMixin
from cl.runtime.records.type_util import TypeUtil


class QueryMixin(PartitionMixin, ABC):
    """Optional mixin for a query."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @classmethod
    @abstractmethod
    def get_target_type(cls) -> type:
        """The query will return only the subtypes of this type (each derived query must override)."""

    def get_table(self) -> str:
        """Return table name for this record as a PascalCase string, return key type name by default."""
        return TypeUtil.name(self.get_target_type().get_key_type())
