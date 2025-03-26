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
from cl.runtime.contexts.db_context import _KEY_SERIALIZER
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.qa.pytest.pytest_fixtures import pytest_celery_queue  # noqa
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.tasks.run_error_response_item import RunErrorResponseItem
from cl.runtime.routers.tasks.run_request import RunRequest
from cl.runtime.routers.tasks.run_response_item import RunResponseItem
from cl.runtime.serializers.string_serializer import StringSerializer
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubHandlers

stub_handlers = StubHandlers()
key_serializer = StringSerializer()
key_str = _KEY_SERIALIZER.serialize(stub_handlers)

simple_requests = [
    {
        "db": "DEPRECATED",  # TODO: Review and remove
        "dataset": "",
        "table": "StubHandlers",
        "keys": [key_str],
        "method": "InstanceHandler1b",
    },
    {
        "dataset": "",
        "table": "StubHandlers",
        "method": "StaticHandler1a",
    },
]

save_to_db_requests = [
    {
        "db": "DEPRECATED",  # TODO: Review and remove
        "dataset": "",
        "table": "StubHandlers",
        "keys": [key_str],
        "method": "HandlerSaveToDb",
    }
]

expected_records_in_db = [[StubDataclassRecord(id="saved_from_handler")]]


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_method(pytest_celery_queue):
    """Test coroutine for /tasks/run route."""

    DbContext.save_one(stub_handlers)

    for request in simple_requests + save_to_db_requests:
        request_object = RunRequest(**request)
        result = RunResponseItem.run_tasks(request_object)

        assert isinstance(result, list)

        for result_item in result:
            assert isinstance(result_item, (RunResponseItem, RunErrorResponseItem))
            assert result_item.task_run_id is not None

            if request_object.keys:
                assert result_item.key is not None
                assert result_item.key in request_object.keys

    for request, expected_records in zip(save_to_db_requests, expected_records_in_db):
        expected_keys = [rec.get_key() for rec in expected_records]

        request_object = RunRequest(**request)
        response_items = RunResponseItem.run_tasks(request_object)
        [Task.wait_for_completion(TaskKey(task_id=response_item.task_run_id)) for response_item in response_items]
        actual_records = list(DbContext.load_many(StubDataclassRecord, expected_keys))
        assert actual_records == expected_records


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_api(pytest_celery_queue):
    """Test REST API for /tasks/run route."""

    DbContext.save_one(stub_handlers)

    with QaClient() as test_client:
        for request in simple_requests + save_to_db_requests:
            response = test_client.post("/tasks/run", json=request)
            assert response.status_code == 200
            result = response.json()

            # Check that the result is a list
            assert isinstance(result, list)

            # Check if each item in the result has valid data to construct RunResponseItem
            for item in result:
                RunResponseItem(**item)
                assert item.get("TaskRunId") is not None

                if request.get("keys"):
                    assert item.get("Key") is not None
                    assert item.get("Key") in request["keys"]

        for request, expected_records in zip(save_to_db_requests, expected_records_in_db):
            expected_keys = [rec.get_key() for rec in expected_records]

            test_client.post("/tasks/run", json=request)
            request_object = RunRequest(**request)
            response_items = RunResponseItem.run_tasks(request_object)
            [Task.wait_for_completion(TaskKey(task_id=response_item.task_run_id)) for response_item in response_items]
            actual_records = list(DbContext.load_many(StubDataclassRecord, expected_keys))
            assert actual_records == expected_records


if __name__ == "__main__":
    pytest.main([__file__])
