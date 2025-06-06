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
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True)
class TableKey(DataMixin):
    """
    Specifies the table where a record is stored.

    Notes:
        This class is derived from DataMixin directly rather than KeyMixin to avoid a cyclic reference.
    """

    table_id: str = required()
    """Globally unique table identifier across all key types."""

    @classmethod
    def get_key_type(cls) -> type:
        """Return key type even when called from a record."""
        return TableKey

    def get_table(self) -> "TableKey":
        """Returns key class name as table name, key class may override to make the table dependent on its fields."""
        return TableKey(table_id=TypeUtil.name(self.get_key_type()))
