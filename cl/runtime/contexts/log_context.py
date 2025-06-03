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
from cl.runtime.records.for_dataclasses.extensions import optional


@dataclass(slots=True, kw_only=True)
class LogContext(Context):
    """Provides get_logger() method returning a configured logger."""

    handler: str | None = optional()
    """Name of the called handler."""

    type: str | None = optional()
    """Type name."""

    record_key: str | None = optional()
    """Key of the record on which the handler is run."""

    task_run_id: str | None = optional()
    """Task run id."""

    @classmethod
    def get_base_type(cls) -> type:
        return LogContext

    @classmethod
    def get_logger(
        cls,
        *,
        module_name: str,
    ) -> logging.Logger:
        """Get logger for the specified module name, invoke with __name__ as the argument."""
        return logging.getLogger(module_name)
