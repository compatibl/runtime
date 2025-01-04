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
from cl.runtime.contexts.context import Context


@dataclass(slots=True, kw_only=True)
class LogContext(Context):
    """Provides get_logger() method returning a configured logger."""

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "Log"

    @classmethod
    def get_logger(
        cls,
        *,
        module_name: str,
    ) -> logging.Logger:
        """Get logger for the specified module name, invoke with __name__ as the argument."""
        return logging.getLogger(module_name)
