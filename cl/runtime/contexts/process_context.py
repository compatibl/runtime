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
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.data_mixin import DataMixin


@dataclass(slots=True, kw_only=True)
class ProcessContext(DataMixin):
    """Provides information about the currently running test."""

    testing: bool | None = None
    """True for the root process or worker processes of a test, False when not a test."""

    @classmethod
    def get_base_type(cls) -> type:
        return ProcessContext

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.testing is None:
            # Can be set here based on detecting the root process of a test because ContextSnapshot
            # will initialize this field for the worker processes launched by the test
            self.testing = QaUtil.is_test_root_process()
