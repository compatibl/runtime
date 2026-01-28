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
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin


@dataclass(slots=True, eq=False)
class FilterKey(DataclassMixin, KeyMixin):
    """Performs filtering of records for the specified type."""

    filter_id: str = required()
    """Unique filter identifier for the key type."""

    key_type_name: str = required()
    """Name of the key type for which the filter is specified."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return FilterKey
