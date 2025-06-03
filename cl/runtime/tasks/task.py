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

import datetime as dt
import time
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.contexts.log_context import LogContext
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.sse.event_type import EventType
from cl.runtime.sse.task_event import TaskEvent
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from cl.runtime.tasks.task_status import TaskStatus


@dataclass(slots=True, kw_only=True)
class Task(TaskKey, RecordMixin[TaskKey], ABC):
    """
    The task 'run_task' method is invoked by the queue to which the task is submitted.

    Notes:
        - The task may run sequentially or in parallel with other tasks
        - The task may run in a different process, thread or machine than the submitting code
          and must be able to acquire the resources required by its 'run_task' method in all of these cases
        - The queue updates 'status' field of the task as it progresses from its initial Pending state through
          the Running and optionally Paused state and ending in one of Completed, Failed, or Cancelled states
    """

    label: str | None = None  # TODO: Make required
    """Label for information purposes only (should not be used in processing)."""

    queue: TaskQueueKey = required()
    """The queue that will run the task once it is saved."""

    status: TaskStatus = required()
    """Begins from Pending, continues to Running or Paused, and ends with Completed, Failed, or Cancelled."""

    progress_pct: float = required()
    """Task progress in percent from 0 to 100."""

    elapsed_sec: float | None = None
    """Elapsed time in seconds if available."""

    remaining_sec: float | None = None
    """Remaining time in seconds if available."""

    error_message: str | None = None
    """Error message for Failed status if available."""

    def get_key(self) -> TaskKey:
        return TaskKey(task_id=self.task_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Set or validate task_id
        if self.task_id is None:
            # Automatically generate time-ordered unique task run identifier in UUIDv7 format if not specified
            self.task_id = Timestamp.create()
        else:
            # Otherwise validate
            Timestamp.validate(self.task_id, value_name="task_id", data_type="TaskKey")

        # Set status and progress_pct if not yet set
        if self.status is None:
            self.status = TaskStatus.PENDING
        if self.progress_pct is None:
            self.progress_pct = 0.0

    @abstractmethod
    def _execute(self) -> None:
        """Run payload without updating status or handling exceptions (protected, callers should invoke 'run_task')."""

    def _create_log_context(self) -> LogContext:
        """Create LogContext with task specific info."""
        return LogContext(task_run_id=self.task_id).build()

    def run_task(self) -> None:
        """Invoke execute with task status updates and exception handling."""
        logger = LogContext.get_logger(module_name=__name__)

        with self._create_log_context():
            try:
                logger.info("Start task execution.", extra={"event": TaskEvent(event_type=EventType.TASK_STARTED)})

                # Save with Running status
                update = self.clone()
                update.status = TaskStatus.RUNNING
                DbContext.save_one(update.build())

                # Invoke out-of-process execution of payload
                self._execute()

            except Exception as e:  # noqa

                logger.error(
                    "Task failed with exception.",
                    exc_info=True,
                    extra={"event": TaskEvent(event_type=EventType.TASK_FINISHED)},
                )

                # Save with Failed status and execution info
                update = self.clone()
                update.status = TaskStatus.FAILED
                update.progress_pct = 100.0
                update.elapsed_sec = 0.0  # TODO: Implement
                update.remaining_sec = 0.0
                update.error_message = str(e)
                DbContext.save_one(update.build())
            else:

                logger.info(
                    "Task completed successfully.", extra={"event": TaskEvent(event_type=EventType.TASK_FINISHED)}
                )

                # Record the end time
                end_time = DatetimeUtil.now()

                # Save with Completed status and execution info
                # Save with Failed status and execution info
                update = self.clone()
                update.status = TaskStatus.COMPLETED
                update.progress_pct = 100.0
                update.elapsed_sec = 0.0  # TODO: Implement
                update.remaining_sec = 0.0
                DbContext.save_one(update.build())

    @classmethod
    def wait_for_completion(cls, task_key: TaskKey, timeout_sec: int = 10) -> None:  # TODO: Rename or move
        """Wait for completion of the specified task run before exiting from this method (not async/await)."""

        start_datetime = DatetimeUtil.now()
        while DatetimeUtil.now() < start_datetime + dt.timedelta(seconds=timeout_sec):
            task = DbContext.load_one(Task, task_key)
            if task.status == TaskStatus.COMPLETED:
                # Test success, task has been completed
                return
            # TODO: Refactor to use queue-specific push communication rather than heartbeat
            time.sleep(1)  # Sleep for 1 second to reduce CPU load

        # Test failure
        raise RuntimeError(f"Task has not been completed after {timeout_sec} sec.")
