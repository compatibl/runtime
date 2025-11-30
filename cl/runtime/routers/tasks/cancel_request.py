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

from __future__ import annotations
from cl.runtime.routers.context_request import ContextRequest


class CancelRequest(ContextRequest):
    """Request data type for the /tasks/cancel route."""

    task_run_ids: list[str] = []
    """List of task run ids to cancel."""

    cancel_all: bool = False
    """Flag indicating if all running tasks should be cancelled."""
