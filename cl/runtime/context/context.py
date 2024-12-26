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
from typing import Dict
from cl.runtime.context.base_context import BaseContext


@dataclass(slots=True, kw_only=True)
class Context(BaseContext):
    """Protocol implemented by context objects providing logging, database, dataset, and progress reporting."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Context"

    def _current_context_field_not_set_error(self, field_name: str) -> None:
        """Error message about a Context field not set."""
        # Get context stack for the current asynchronous environment
        context_stack = self._get_context_stack()
        if not context_stack:
            raise RuntimeError(
                f"""
Field '{field_name}' of the context class '{type(self).__name__}' is not set.
The context in the outermost 'with' clause (root context) must set all fields
of the Context class. Inside the 'with' clause, these fields will be populated
from the current context.
"""
            )
