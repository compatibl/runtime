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

import pytest
from unittest.mock import MagicMock
from unittest.mock import patch
from celery.exceptions import Reject
from cl.runtime.contexts.context_manager import active
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.db.data_source import DataSource
from cl.runtime.tasks.celery.celery_queue import CeleryQueue
from cl.runtime.tasks.celery.celery_queue import execute_task
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers


def _create_task(queue: TaskQueueKey) -> TaskKey:
    """Create a test task."""

    method_callable = StubHandlers.run_static_method_1a
    task = ClassMethodTask.create(queue=queue, record_type=StubHandlers, method_callable=method_callable).build()
    active(DataSource).replace_one(task, commit=True)
    return task.get_key()


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_method(celery_queue_fixture):
    """Test calling 'execute_task' method in-process."""

    # Create queue
    queue_id = f"test_celery_queue.test_method"
    queue = CeleryQueue(queue_id=queue_id)
    active(DataSource).replace_one(queue, commit=True)

    # Create task
    task_key = _create_task(queue.get_key())

    # Call 'execute_task' method in-process
    context_snapshot_data = ContextSnapshot.to_json()
    execute_task(
        task_key.task_id,
        context_snapshot_data,
    )


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_api(celery_queue_fixture):
    """Test submitting task for execution out of process."""
    # Create queue
    queue_id = f"test_celery_queue.test_api"
    queue = CeleryQueue(queue_id=queue_id)
    active(DataSource).replace_one(queue, commit=True)

    # Create task
    task_key = _create_task(queue.get_key())

    # Submit task and check for its completion
    queue.submit_task(task_key)
    Task.wait_for_completion(task_key)


def test_reached_tenant_limit(default_db_fixture):
    """Test reached tenant limit of tasks."""
    context_snapshot_json = ContextSnapshot.capture_active().to_json()

    mock_instance = MagicMock(celery_max_tenant_tasks=0)
    mock_instance.celery_max_tenant_tasks = 0
    with patch("cl.runtime.tasks.celery.celery_queue.celery_settings", new=mock_instance):
        with pytest.raises(Reject):
            execute_task(
                "test_task_id",
                context_snapshot_json,
            )


if __name__ == "__main__":
    pytest.main([__file__])
