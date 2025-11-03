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

from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.stats.condition_key import ConditionKey


@dataclass(slots=True, kw_only=True)
class Condition(ConditionKey, RecordMixin):
    """Condition under which an experiment is performed."""

    label: str = required()
    """Short label to use in charts and reporting, defaults to condition_id."""

    def get_key(self) -> ConditionKey:
        return ConditionKey(condition_id=self.condition_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.label is None:
            # Use condition_id as label if not specified
            self.label = self.condition_id
