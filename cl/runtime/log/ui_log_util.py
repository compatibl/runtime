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
from typing import Any
from typing import Iterable
from typing_extensions import Final
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.events.sse_query_util import SseQueryUtil
from cl.runtime.log.log_message import LogMessage
from cl.runtime.log.task_logs import TaskLogs
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_query import TaskQuery
from cl.runtime.tasks.task_status import TaskStatus

# Create serializers
_UI_SERIALIZER = DataSerializers.FOR_UI

_LOG_HISTORY_LIMIT: Final[int] = 1000


@dataclass(slots=True, kw_only=True)
class UiLogUtil(DataMixin):
    """UI logs util class."""

    @classmethod
    def run_get_flat_logs(cls) -> dict[str, Any]:
        """Return a list of the last N log messages, sorted by timestamp in ascending order."""

        log_messages = reversed(
            list(SseQueryUtil.query_sorted_desc_and_limited(LogMessage().get_key_type(), limit=_LOG_HISTORY_LIMIT))
        )
        return cls._wrap_to_result(log_messages)

    @classmethod
    def run_get_error_logs(cls) -> dict[str, Any]:
        """Return a list of the last N error log messages, sorted by timestamp in ascending order."""

        log_messages = reversed(
            [
                x
                for x in SseQueryUtil.query_sorted_desc_and_limited(
                    LogMessage().get_key_type(), limit=_LOG_HISTORY_LIMIT
                )
                if x.level.lower() == "error"
            ]
        )
        return cls._wrap_to_result(log_messages)

    @classmethod
    def _get_task_status(cls, task_run_id: str) -> TaskStatus:
        """Return task status by its run_id."""

        target_task_query = TaskQuery(task_id=task_run_id).build()
        tasks = list(active(DataSource).load_by_query(target_task_query))

        if not tasks:
            raise RuntimeError(f"Not found task for {task_run_id=}")
        elif len(tasks) > 1:
            raise RuntimeError(f"Found more than one task for {task_run_id=}")

        task = tasks[0]
        return task.status

    @classmethod
    def run_get_logs_by_task(cls) -> dict[str, Any]:
        """Return last N log messages aggregated by task_run_id and sorted by timestamp in ascending order."""

        result = {}
        for log_message in reversed(
            list(SseQueryUtil.query_sorted_desc_and_limited(LogMessage().get_key_type(), limit=_LOG_HISTORY_LIMIT))
        ):
            task_run_id = log_message.task_run_id

            if task_run_id is None:
                continue

            if task_run_id not in result:
                task_status = cls._get_task_status(task_run_id)
                result[task_run_id] = TaskLogs(
                    task_run_id=task_run_id,
                    record_type_name=log_message.record_type_name,
                    record_key=log_message.record_key,
                    handler_name=log_message.handler_name,
                    status=task_status,
                    logs=[],
                )

            result[task_run_id].logs.append(log_message)

        return cls._wrap_to_result(result.values())

    @classmethod
    def _wrap_to_result(cls, result: Iterable[Any]) -> dict[str, Any]:
        serialized_result = list(_UI_SERIALIZER.serialize(x) for x in result)
        return {"Result": serialized_result}
