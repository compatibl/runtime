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
from typing_extensions import Final
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.log.log_message import LogMessage
from cl.runtime.log.task_logs import TaskLogs
from cl.runtime.log.ui_clear_logs_marker import UiClearLogsMarker
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.tasks.task_query import TaskQuery
from cl.runtime.tasks.task_status import TaskStatus

# Create serializers
_UI_SERIALIZER = DataSerializers.FOR_UI

_LOG_HISTORY_LIMIT: Final[int] = 1000


@dataclass(slots=True, kw_only=True)
class UiLogUtil(DataclassMixin):
    """UI logs util class."""

    @classmethod
    def run_get_flat_logs(cls) -> list[dict[str, Any]]:
        """Return a list of the last N log messages, sorted by timestamp in ascending order."""
        log_messages = cls._get_ui_logs()
        log_messages = log_messages[::-1]

        return list(_UI_SERIALIZER.serialize(x) for x in log_messages)

    @classmethod
    def run_get_error_logs(cls) -> list[dict[str, Any]]:
        """Return a list of the last N error log messages, sorted by timestamp in ascending order."""
        log_messages = cls._get_ui_logs()
        log_messages = [log for log in log_messages if log.level.lower() == "error"]
        log_messages = log_messages[::-1]

        return list(_UI_SERIALIZER.serialize(x) for x in log_messages)

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
    def run_get_logs_by_task(cls) -> list[dict[str, Any]]:
        """Return last N log messages aggregated by task_run_id and sorted by timestamp in ascending order."""

        result = {}

        # TODO (Roman): Ensure consistency when part of the Task logs have been purged
        log_messages = cls._get_ui_logs()
        log_messages = log_messages[::-1]

        for log_message in log_messages:
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

        return list(_UI_SERIALIZER.serialize(x) for x in result.values())

    @classmethod
    def run_clear_logs(cls) -> None:
        """Save clear logs marker with Timestamp of now."""
        clear_logs_timestamp = UiClearLogsMarker().build()
        active(DataSource).replace_one(clear_logs_timestamp, commit=True)

    @classmethod
    def _get_last_clear_logs_timestamp(cls) -> UiClearLogsMarker | None:
        """Get last ClearLogsMarker record or None if not found."""

        # Get UiClearLogsMarker by query with limit 1
        clear_logs_timestamps = active(DataSource).load_all(
            key_type=UiClearLogsMarker().get_key_type(),
            limit=1,
            sort_order=SortOrder.DESC,
        )

        # If UiClearLogsMarker record is not found, return None
        if clear_logs_timestamps:
            return clear_logs_timestamps[0]
        else:
            return None

    @classmethod
    def _get_ui_logs(cls) -> tuple[LogMessage, ...]:
        """Get last LogMessage records sorted by DESC. Filter logs by UiClearLogsMarker if exists."""

        logs = active(DataSource).load_all(
            key_type=LogMessage().get_key_type(), limit=_LOG_HISTORY_LIMIT, sort_order=SortOrder.DESC
        )

        # Filter out logs created before cleaning
        clear_logs = cls._get_last_clear_logs_timestamp()
        if clear_logs is not None:
            for i, log in enumerate(logs):
                if log.timestamp <= clear_logs.clear_logs_timestamp:
                    return logs[:i]

        return logs
