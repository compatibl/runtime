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
from cl.runtime.contexts.context_mixin import ContextMixin
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class ProcessContext(ContextMixin, DataMixin):
    """Provides information about the currently running test."""

    testing: bool = False
    """True inside a test, False otherwise (this field is passed to out-of-process tasks)."""

    env_name: str = required()
    """Used to set database name and similar parameters (this field is passed to out-of-process tasks)."""

    @classmethod
    def get_base_type(cls) -> type:
        return ProcessContext

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # If not specified, set based on the current context
        if self.testing is None:
            self.testing = self.is_testing()
        if self.env_name is None:
            self.env_name = self.get_env_name()

    @classmethod
    def is_testing(cls) -> bool:
        """Return test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""
        if (current_context := ProcessContext.current_or_none()) is not None:
            # Get from the current ProcessContext if exists
            return current_context.testing
        else:
            # Otherwise set based on the current process
            return Settings.is_inside_test

    def get_env_name(self) -> str:
        """Return test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""
        if (current_context := ProcessContext.current_or_none()) is not None:
            # Get from the current ProcessContext if exists
            return current_context.env_name
        else:
            # Otherwise set based on the current process
            if Settings.is_inside_test:
                # Return test_module.test_module or test_module.test_class.test_method inside a test
                return QaUtil.get_test_name()
            else:
                return DbSettings.instance().db_id  # TODO: Pass f-string parameters
