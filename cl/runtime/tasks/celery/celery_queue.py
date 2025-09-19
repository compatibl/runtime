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

import logging.config
import multiprocessing
import os
from dataclasses import dataclass
from typing import Dict
from typing import Final
from urllib.parse import urlparse
import redis
from celery import Celery
from celery.signals import setup_logging
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.log_config import celery_empty_logging_config
from cl.runtime.log.log_config import logging_config
from cl.runtime.server.env import Env
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_queue import TaskQueue

CELERY_RUN_COMMAND_QUEUE: Final[str] = "run_command"

celery_settings = CelerySettings.instance()

celery_app = Celery(
    "worker",
    broker=celery_settings.celery_broker_uri,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_track_started = True
celery_app.conf.task_default_queue = celery_settings.celery_broker_queue
celery_app.conf.task_time_limit = celery_settings.celery_time_limit


@setup_logging.connect()
def config_loggers(*args, **kwargs):
    """Setup logging config for celery worker."""
    from logging.config import dictConfig

    # Use empty config to suppress celery logger and propagate to root.
    dictConfig(celery_empty_logging_config)


@celery_app.task(max_retries=celery_settings.celery_max_retries)  # Do not retry failed tasks
def execute_task(
    task_id: str,
    context_snapshot_json: str,
) -> None:
    """Invoke 'run_task' method of the specified task."""

    # Deserialize context from 'context_data' parameter to run with the same settings as the caller context
    with ContextSnapshot.from_json(context_snapshot_json):

        # Load and run the task
        task_key = TaskKey(task_id=task_id).build()
        task = active(DataSource).load_one(task_key, cast_to=Task)
        task.run_task()


def celery_start_queue_callable(*, log_config: Dict) -> None:
    """
    Callable for starting the celery queue process.

    Args:
        log_config: logging dict config from the main process.
    """

    # Setup logging config from the main process.
    logging.config.dictConfig(log_config)

    celery_app.worker_main(
        argv=[
            "-A",
            "cl.runtime.tasks.celery.celery_queue",
            "worker",
            "--loglevel=info",
            f"--pool={celery_settings.celery_pool_type}",
            f"--concurrency={celery_settings.celery_workers}",
        ],
    )


def celery_delete_existing_tasks() -> None:
    """Delete the existing Celery tasks (will exit when the current process exits)."""

    # Remove sqlite file of celery broker if exists
    if celery_settings.celery_broker == "sqlite":
        celery_file = celery_settings.celery_broker_uri.split("sqlite:///")[1]

        # Remove sqlite file of celery broker if exists
        if os.path.exists(celery_file):
            os.remove(celery_file)

    if celery_settings.celery_broker == "redis":
        # Parse the URI
        parsed_uri = urlparse(celery_settings.celery_broker_uri)
        host = parsed_uri.hostname
        port = parsed_uri.port
        db = parsed_uri.path.lstrip("/")

        # Connect to Redis
        redis_client = redis.StrictRedis(host=host, port=port, db=db)

        # Clear the Celery queue and result backend
        redis_client.delete(celery_settings.celery_broker_queue)
        redis_client.flushdb()


def celery_start_queue() -> None:
    """
    Start Celery workers (will exit when the current process exits).

    Args:
        log_dir: Directory where Celery console log file will be written
    """
    worker_process = multiprocessing.Process(
        target=celery_start_queue_callable, daemon=True, kwargs={"log_config": logging_config}
    )
    worker_process.start()


@dataclass(slots=True, kw_only=True)
class CeleryQueue(TaskQueue):
    """Execute tasks using Celery."""

    # max_workers: int = required()  # TODO: Implement support for max_workers
    """The maximum number of processes running concurrently."""

    # TODO: @abstractmethod
    def run_start_queue(self) -> None:
        """Start queue workers."""

    # TODO: @abstractmethod
    def run_stop_queue(self) -> None:
        """Cancel all active runs and stop queue workers."""

    def submit_task(self, task: TaskKey):

        # Wrap into Env
        with activate(Env().build()):

            # Get and serialize current context
            context_snapshot_json = ContextSnapshot.capture_active().to_json()

            # Pass parameters to the Celery task signature
            execute_task_signature = execute_task.s(
                task.task_id,
                context_snapshot_json,
            )

            # Submit task to Celery with completed and error links
            execute_task_signature.apply_async(
                retry=False,  # Do not retry in case the task fails
                ignore_result=True,  # TODO: Do not publish to the Celery result backend
            )
