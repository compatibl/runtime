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
from typing import Dict
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.tasks.result_request import ResultRequest
from cl.runtime.routers.tasks.result_response_item import ResultResponseItem
from cl.runtime.routers.tasks.submit_response_item import handler_queue
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from stubs.cl.runtime import StubHandlers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers_key import StubHandlersKey


def _save_tasks_and_get_requests() -> list[Dict]:
    """Creates and saves tasks."""

    # Create handler tasks
    queue_key = handler_queue.get_key()
    tasks = [
        InstanceMethodTask.create(
            queue=queue_key,
            record_or_key=StubHandlersKey(stub_id=f"{i}").build(),
            method_callable=StubHandlers.run_instance_method_1a,
        ).build()
        for i in range(2)
    ]
    active(DataSource).save_many(tasks)

    requests = [
        {
            "task_run_ids": [str(task.task_id) for task in tasks],
            "dataset": "",
        }
    ]
    return requests


def test_method(default_db_fixture):
    """Test coroutine for /tasks/result route."""

    for request in _save_tasks_and_get_requests():
        request_obj = ResultRequest(**request)
        result = ResultResponseItem.get_response(request_obj)

        assert isinstance(result, list)
        for result_response_item, task_run_id in zip(result, request_obj.task_run_ids):

            # Validate type.
            assert isinstance(result_response_item, ResultResponseItem)

            # Validate fields.
            assert result_response_item.key == task_run_id
            assert result_response_item.task_run_id == task_run_id
            assert result_response_item.result is not None


def test_api(default_db_fixture):
    """Test REST API for /tasks/result route."""

    with QaClient() as test_client:
        for request in _save_tasks_and_get_requests():
            response = test_client.post("/tasks/result", json=request)
            assert response.status_code == 200

            result = response.json()

            assert isinstance(result, list)
            request_obj = ResultRequest(**request)
            for result_item, task_run_id in zip(result, request_obj.task_run_ids):

                # Validate with Pydantic.
                result_response_item = ResultResponseItem(**result_item)

                # Validate fields.
                assert result_response_item.key == task_run_id
                assert result_response_item.task_run_id == task_run_id
                assert result_response_item.result is not None


if __name__ == "__main__":
    pytest.main([__file__])
