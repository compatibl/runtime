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
from typing import Tuple
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_table import StubDataclassPolymorphicTable


@dataclass(slots=True)
class StubDataclassPolymorphicKey(StubDataclassPolymorphicTable):
    """Specifies the table where this record is stored and the key within that table."""

    table_field: str = required()
    """Determines the table where this record is stored."""

    key_field: str = required()
    """Unique within this table where this record is stored."""

    @classmethod
    def get_key_type(cls) -> type:
        return StubDataclassPolymorphicKey

    def get_table(self) -> str:
        """Override the default to specify a custom table name."""
        return self.table_field

    def serialize_key(self) -> Tuple:
        return self.table_field, self.key_field
