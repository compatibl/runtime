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
import multiprocessing
from celery import Celery
from cl.runtime import Context
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.ordered_uuid import OrderedUuid
from cl.runtime.records.protocols import is_record
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.storage.data_source_types import TDataDict
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_queue import TaskQueue
from cl.runtime.tasks.task_run import TaskRun
from cl.runtime.tasks.task_run_key import TaskRunKey
from cl.runtime.tasks.task_status import TaskStatus
from dataclasses import dataclass
from orjson import orjson
from pymongo import MongoClient
from typing import Final
from uuid import UUID

CELERY_MAX_WORKERS = 4

CELERY_RUN_COMMAND_QUEUE: Final[str] = "run_command"
CELERY_MAX_RETRIES: Final[int] = 3
CELERY_TIME_LIMIT: Final[int] = 3600 * 2  # TODO: 2 hours (configure)

celery_mongo_server_uri = "mongodb://localhost:27017/"  # TODO: Check that server URI ends in slash
celery_mongo_database = "celery"  # TODO: Changing DB name stops Celery queue from working, investigate

celery_app = Celery(
    "worker",
    broker=f"{celery_mongo_server_uri}{celery_mongo_database}",
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_track_started = True

context_serializer = DictSerializer()
"""Serializer for the context parameter of 'execute_task' method."""


@celery_app.task(max_retries=0)  # Do not retry failed tasks
def execute_task(
    task_run_id: str,
    task_id: str,
    queue_id: str,
    context_data: TDataDict,
) -> None:
    """Invoke execute method of the specified task."""

    # Deserialize context from 'context_data' parameter to run with the same settings as the caller context
    with context_serializer.deserialize_data(context_data) as context:
        # Get timestamp from task_run_id
        task_run_uuid = UUID(task_run_id)
        submit_time = OrderedUuid.datetime_of(task_run_uuid)

        # Create a task run record in Pending state
        task_run = TaskRun()
        task_run.task_run_id = task_run_id
        task_run.queue = queue_id
        task_run.task = TaskKey(task_id=task_id)
        task_run.submit_time = submit_time
        task_run.update_time = submit_time
        task_run.status = TaskStatus.Pending
        context.save_one(task_run)

        try:
            # Load and execute the task object
            task_key = TaskKey(task_id=task_id)
            task = context.load_one(Task, task_key)
            task.execute()
        except Exception as e:  # noqa
            # Update task run record to report task failure
            task_run.update_time = DatetimeUtil.now()
            task_run.status = TaskStatus.Failed
            task_run.result = str(e)
            context.save_one(task_run)
        else:
            # Update task run record to report task completion
            task_run.update_time = DatetimeUtil.now()
            task_run.status = TaskStatus.Completed
            context.save_one(task_run)


def celery_start_queue_callable() -> None:
    celery_app.worker_main(
        argv=[
            "-A",
            "cl.runtime.tasks.celery.celery_queue",
            "worker",
            "--loglevel=info",
            f"--autoscale={CELERY_MAX_WORKERS},1",
            f"--pool=solo",  # One concurrent task per worker, do not switch to prefork (not supported on Windows)
            f"--concurrency=1",  # Use only for prefork, one concurrent task per worker (similar to solo)
        ],
    )


def celery_delete_existing_tasks() -> None:
    """Delete the existing Celery tasks (will exit when the current process exits)."""
    client = MongoClient(celery_mongo_server_uri)
    client.drop_database(celery_mongo_database)


def celery_start_queue() -> None:
    """Start Celery workers (will exit when the current process exits)."""
    worker_process = multiprocessing.Process(target=celery_start_queue_callable, daemon=True)
    worker_process.start()


@dataclass(slots=True, kw_only=True)
class CeleryQueue(TaskQueue):
    """Submits tasks to Celery workers."""

    # max_workers: int = missing()  # TODO: Implement support for max_workers
    """The maximum number of processes running concurrently."""

    # TODO: @abstractmethod
    def start_workers(self) -> None:
        """Start queue workers."""

    # TODO: @abstractmethod
    def stop_workers(self) -> None:
        """Cancel all active runs and stop queue workers."""

    # TODO: @abstractmethod
    def cancel_all(self) -> None:
        """Cancel all active runs but do not stop queue workers."""

    # TODO: @abstractmethod
    def pause_all(self) -> None:
        """Do not start new runs and send pause command to the existing runs."""

    # TODO: @abstractmethod
    def resume_all(self) -> None:
        """Resume starting new runs and send resume command to existing runs."""

    def submit_task(self, task: TaskKey) -> TaskRunKey:
        # Get current context
        context = Context.current()

        # Save task if provided as record rather than key
        if is_record(task):
            context.save_one(task)

        # Create task run identifier and convert to string
        task_run_uuid = OrderedUuid.create_one()
        task_run_id = str(task_run_uuid)

        # Pass parameters to the Celery task signature
        context_data = context_serializer.serialize_data(context)
        execute_task_signature = execute_task.s(
            task_run_id,
            task.task_id,
            self.queue_id,
            context_data,
        )

        # Submit task to Celery with completed and error links
        execute_task_signature.apply_async(
            retry=False,  # Do not retry in case the task fails
            ignore_result=True,  # TODO: Do not publish to the Celery result backend
        )

        return TaskRunKey(task_run_id=task_run_id)