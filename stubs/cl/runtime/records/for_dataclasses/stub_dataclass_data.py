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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class StubDataclassData(DataclassMixin):
    """Stub base data type."""

    str_field: str = "abc"
    """Stub field."""

    int_field: int = 123
    """Stub field."""

    _regression_guard: RegressionGuard | None = None
    """Optional regression guard for testing."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self._regression_guard:
            self._regression_guard.write("StubDataclassData.__init")
