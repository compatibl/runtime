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
from cl.runtime.log.log import Log


@dataclass(slots=True, kw_only=True)
class TaskLog(Log):
    """Provides logging for task execution."""

    handler: str | None = None
    """Name of the called handler."""

    record_type: str | None = None
    """Type name."""

    record_key: str | None = None
    """Key of the record on which the handler is run."""

    task_run_id: str | None = None
    """Task run id."""

