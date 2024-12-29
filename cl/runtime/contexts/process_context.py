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
from typing_extensions import Self
from cl.runtime.contexts.context import Context
from cl.runtime.contexts.env_util import EnvUtil
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
class ProcessContext(Context):
    """Provides information about the currently running test."""

    testing: bool = False
    """True inside a test, False otherwise (this field is passed to out-of-process tasks)."""

    env_name: str = required()
    """Used to set database name and similar parameters (this field is passed to out-of-process tasks)."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Process"

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        # If not specified, set based on the current context
        if self.testing is None:
            self.testing = self.is_testing()
        if self.env_name is None:
            self.env_name = self.get_env_name()

        # Return self to enable method chaining
        return self

    @classmethod
    def is_testing(cls) -> bool:
        """Return test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""
        if (current_context := ProcessContext.current_or_none()) is not None:
            # Get from the current ProcessContext if exists
            return current_context.testing
        else:
            # Otherwise set based on the current process
            return Settings.is_inside_test

    @classmethod
    def get_env_name(cls) -> str:
        """Return test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""
        if (current_context := ProcessContext.current_or_none()) is not None:
            # Get from the current ProcessContext if exists
            return current_context.env_name
        else:
            # Otherwise set based on the current process
            if Settings.is_inside_test:
                # Return test_module.test_module or test_module.test_class.test_method inside a test
                return EnvUtil.get_env_name()  # TODO: Move code from EnvUtil
            else:
                # Return None outside a test
                return "main"  # TODO: Use context_id
