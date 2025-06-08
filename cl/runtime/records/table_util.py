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


from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.type_util import TypeUtil


class TableUtil:
    """Utilities for working with tables."""

    @classmethod
    def get_table(cls, key: KeyMixin) -> str:
        """Get table name from type, validate format and remove Key suffix if present."""

        # Get table name from key
        table = key.get_table()

        # Validate PascalCase format
        if not CaseUtil.is_pascal_case(table):
            raise RuntimeError(
                f"Table name {table} for key type {TypeUtil.name(key)} is not in PascalCase format\n"
                f"or does not follow the custom rule for separators in front of digits."
            )

        # Remove Key suffix if present
        # TODO: Restore which will also test that this method is used consistently everywhere
        # if table.endswith("Key"):
        #    table = table.removesuffix("Key")

        return table
