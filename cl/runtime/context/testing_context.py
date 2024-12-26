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
from cl.runtime.context.base_context import BaseContext
from cl.runtime.context.env_util import EnvUtil
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True, init=False)
class TestingContext(BaseContext):
    """Provides information about the currently running test."""

    testing_namespace_or_none: str | None
    """Set to test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Testing"

    def __init__(self):
        """Set test parameters inside test."""

        # Copying to a context instance field ensures the context remains the same for out-of-process tasks
        self.testing_namespace_or_none = self.get_testing_namespace_or_none()

    @classmethod
    def get_testing_namespace_or_none(cls) -> str | None:
        """Return test_module.test_module or test_module.test_class.test_method inside a test, None outside a test."""
        if (current_context := TestingContext.current_or_none()) is not None:
            # Get from the current TestingContext if exists
            return current_context.testing_namespace_or_none
        else:
            # Otherwise get the value from settings based on the current process
            # The code below will not work as expected out-of-process, use 'with TestingContext()' in this case
            if Settings.is_inside_test:
                # Return test_module.test_module or test_module.test_class.test_method inside a test
                return EnvUtil.get_env_name()  # TODO: Move code from EnvUtil
            else:
                # Return None outside a test
                return None
