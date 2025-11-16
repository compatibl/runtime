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
from cl.runtime.stat.case_key import CaseKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Case(CaseKey, RecordMixin):
    """Parameter with a unique identifier."""

    label: str = required()
    """Short label to use in charts and reporting, defaults to param_id."""

    def get_key(self) -> CaseKey:
        return CaseKey(param_id=self.param_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.label is None:
            # Use param_id as label if not specified
            self.label = self.param_id
