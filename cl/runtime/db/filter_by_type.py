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
from cl.runtime.db.filter import Filter
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.type_check import TypeCheck
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_info import TypeInfo


@dataclass(slots=True, kw_only=True)
class FilterByType(Filter):
    """Selects records that are subclass of the specified record type."""

    record_type_name: str = required()
    """The filter selects records that are subclass of the specified record type."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Perform checks
        record_type = TypeInfo.from_type_name(self.record_type_name)
        assert TypeCheck.guard_record_type(record_type)

        # Set key_type_name in this class based on record_type_name
        self.key_type_name = typename(record_type.get_key_type())
