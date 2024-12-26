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

import logging
from dataclasses import dataclass
from typing import Dict
from cl.runtime.backend.core.user_key import UserKey
from cl.runtime.context.base_context import BaseContext
from cl.runtime.db.db_key import DbKey
from cl.runtime.log.log_key import LogKey
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.protocols import is_key


@dataclass(slots=True, kw_only=True)
class Context(BaseContext):
    """Protocol implemented by context objects providing logging, database, dataset, and progress reporting."""

    user: UserKey = missing()
    """Current user, 'Context.current().user' is used if not specified."""

    secrets: Dict[str, str] | None = None
    """Context-specific secrets take precedence over those defined via Dynaconf."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Context"

    def __post_init__(self):
        """Set fields to their values in 'Context.current()' if not specified."""

        # Do not execute this code on deserialized context instances (e.g. when they are passed to a task queue)
        if not self.is_deserialized:
            # Set fields that are not specified as __init__ param to their values from 'Context.current()'

            if self.user is None:
                self._current_context_field_not_set_error("user")
                self.user = Context.current().user

            # Optional fields, set to None if not set in the root context
            # The root context uses ContextSettings values of these fields
            if self.secrets is None:
                self.secrets = Context.current().secrets

        # Return self to enable method chaining
        return self

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

