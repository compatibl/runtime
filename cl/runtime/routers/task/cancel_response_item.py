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
from pydantic import BaseModel
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.events.event_kind import EventKind
from cl.runtime.events.task_finished_event import TaskFinishedEvent
from cl.runtime.log.task_log import TaskLog
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.predicates import In
from cl.runtime.records.typename import typename
from cl.runtime.records.typename import typenameof
from cl.runtime.routers.task.cancel_request import CancelRequest
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_query import TaskQuery
from cl.runtime.tasks.task_queue import TaskQueue
from cl.runtime.tasks.task_status import TaskStatus


class CancelResponseItem(BaseModel):
    """Response data type for the /tasks/cancel route."""

    task_run_id: str
    """Task run id."""

    status_code: str
    """Task status after cancel operation."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_response(cls, request: CancelRequest) -> list[CancelResponseItem]:
        """Cancel tasks in request and return response."""
        tasks = cls._get_tasks_to_cancel(request)

        if not tasks:
            return []

        # Separate cancellable and non-cancellable tasks
        cancellable_tasks = []
        non_cancellable_tasks = []

        for task in tasks:
            if cls._is_cancellable(task):
                cancellable_tasks.append(task)
            else:
                non_cancellable_tasks.append(task)

        # Batch cancel all cancellable tasks
        if cancellable_tasks:
            cls._cancel_tasks_batch(cancellable_tasks)

        # Build response
        response_items = [cls._create_cancelled_response(task) for task in cancellable_tasks] + [
            cls._create_current_status_response(task) for task in non_cancellable_tasks
        ]

        return response_items

    @classmethod
    def _get_tasks_to_cancel(cls, request: CancelRequest) -> list[Task]:
        """Get tasks to cancel based on request type."""
        if hasattr(request, "cancel_all") and request.cancel_all:
            return cls._get_all_active_tasks()
        else:
            return cls._get_tasks_by_ids(request.task_run_ids)

    @classmethod
    def _get_all_active_tasks(cls) -> list[Task]:
        """Get all active tasks that can be cancelled."""
        active_statuses = [TaskStatus.RUNNING, TaskStatus.AWAITING, TaskStatus.PENDING]
        query = TaskQuery(status=In(active_statuses)).build()
        return list(active(DataSource).load_by_query(query, cast_to=Task))

    @classmethod
    def _get_tasks_by_ids(cls, task_run_ids: list[str]) -> list[Task]:
        """Get tasks by their run IDs."""
        task_keys = [TaskKey(task_id=task_id).build() for task_id in task_run_ids]
        return list(active(DataSource).load_many(task_keys, cast_to=Task))

    @classmethod
    def _is_cancellable(cls, task: Task) -> bool:
        """Check if task can be cancelled."""
        cancellable_statuses = (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.AWAITING)
        return task.status in cancellable_statuses

    @classmethod
    def _cancel_task(cls, task: Task, task_queue: TaskQueue) -> None:
        """Cancel a single task."""
        task_queue.cancel_task(task.task_id)
        cls._send_cancellation_event(task)
        cls._update_task_status(task)

    @classmethod
    def _cancel_tasks_batch(cls, tasks: list[Task]) -> None:
        """Cancel multiple tasks using batch operations."""
        if not tasks:
            return

        task_ids = [task.task_id for task in tasks]

        # Revoke in queue
        active(TaskQueue).cancel_tasks_batch(task_ids)  # type: ignore[type-var]

        # Update DB and send events
        updated_tasks = []
        for task in tasks:
            updated = task.clone()
            updated.status = TaskStatus.CANCELLED
            updated.error_message = "Task cancelled by user."
            updated_tasks.append(updated.build())
            cls._send_cancellation_event(task)

        active(DataSource).replace_many(updated_tasks, commit=True)

    @classmethod
    def _create_cancelled_response(cls, task: Task) -> CancelResponseItem:
        """Create response item for cancelled task."""
        return CancelResponseItem(
            status_code="Cancelled",
            task_run_id=str(task.task_id),
        )

    @classmethod
    def _create_current_status_response(cls, task: Task) -> CancelResponseItem:
        """Create response item with current task status."""
        return CancelResponseItem(
            status_code=task.status.name,
            task_run_id=str(task.task_id),
        )

    @classmethod
    def _send_cancellation_event(cls, task: Task) -> None:
        """Send SSE event about task cancellation."""
        event_broker = active(EventBroker)
        events_topic = "events"

        # Determine record_type_name and record_key based on task type
        record_type_name, record_key = cls._get_task_record_info(task)

        # Create TaskLog context to properly populate TaskEvent fields
        task_log = TaskLog(
            task_run_id=task.task_id,
            record_type_name=record_type_name,
            handler=task.method_name if hasattr(task, "method_name") else None,
            record_key=record_key,
        ).build()

        with activate(task_log):
            event_broker.sync_publish(
                events_topic,
                TaskFinishedEvent(
                    event_kind=EventKind.TASK_FINISHED,
                    status=TaskStatus.CANCELLED,
                ).build(),
            )

    @classmethod
    def _get_task_record_info(cls, task: Task) -> tuple[str, str | None]:
        """Get record type name and key for a task."""
        if isinstance(task, InstanceMethodTask):
            record_type_name = typenameof(task.key)
            record_key = KeySerializers.DELIMITED.serialize(task.key)
        elif isinstance(task, ClassMethodTask):
            record_type_name = typename(task.type_)
            record_key = None
        else:
            # Fallback for other task types
            record_type_name = task.__class__.__name__
            record_key = None

        return record_type_name, record_key

    @classmethod
    def _update_task_status(cls, task: Task) -> None:
        """Update task status to CANCELLED in database."""
        update = task.clone()  # For safety, clone the task before updating
        update.status = TaskStatus.CANCELLED
        update.error_message = "Task cancelled by user."
        active(DataSource).replace_one(update.build(), commit=True)
