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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.routers.tasks.submit_response_item import SubmitResponseItem
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.tasks.task import Task
from cl.runtime.tasks.task_key import TaskKey
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubHandlers


def get_simple_requests(key_str: str):
    """Get requests for testing."""
    return [
        {
            "dataset": "",
            "type": "StubHandlers",
            "keys": [key_str],
            "method": "run_instance_method_1b",
        },
        {
            "dataset": "",
            "type": "StubHandlers",
            "method": "run_static_method_1a",
        },
    ]


def get_save_to_db_requests(key_str: str):
    """Get requests for testing."""
    return [
        {
            "dataset": "",
            "type": "StubHandlers",
            "keys": [key_str],
            "method": "run_save_to_db",
        }
    ]


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_method(default_db_fixture, celery_queue_fixture):
    """Test coroutine for /tasks/run route."""

    stub_handlers = StubHandlers().build()
    key_str = KeySerializers.DELIMITED.serialize(stub_handlers.get_key())
    active(DataSource).save_one(stub_handlers)

    for request in get_simple_requests(key_str) + get_save_to_db_requests(key_str):
        request_object = SubmitRequest(**request)
        result = SubmitResponseItem.get_response(request_object)

        assert isinstance(result, list)

        for result_item in result:
            assert isinstance(result_item, SubmitResponseItem)
            assert result_item.task_run_id is not None

            if request_object.keys:
                assert result_item.key is not None
                assert result_item.key in request_object.keys

    expected_records_in_db = [[StubDataclass(id="saved_from_handler")]]
    for request, expected_records in zip(get_save_to_db_requests(key_str), expected_records_in_db):
        expected_keys = [rec.get_key() for rec in expected_records]

        request_object = SubmitRequest(**request)
        response_items = SubmitResponseItem.get_response(request_object)
        [
            Task.wait_for_completion(TaskKey(task_id=response_item.task_run_id).build())
            for response_item in response_items
        ]
        actual_records = list(active(DataSource).load_many(expected_keys))
        assert actual_records == expected_records


@pytest.mark.skip("Celery tasks lock sqlite db file.")  # TODO (Roman): resolve conflict
def test_api(celery_queue_fixture):
    """Test REST API for /tasks/submit route."""

    stub_handlers = StubHandlers()
    key_str = KeySerializers.DELIMITED.serialize(stub_handlers.get_key())
    active(DataSource).save_one(stub_handlers)

    with QaClient() as test_client:
        for request in get_simple_requests(key_str) + get_save_to_db_requests(key_str):
            response = test_client.post("/tasks/submit", json=request)
            assert response.status_code == 200
            result = response.json()

            # Check that the result is a list
            assert isinstance(result, list)

            # Check if each item in the result has valid data to construct SubmitResponseItem
            for item in result:
                SubmitResponseItem(**item)
                assert item.get("TaskRunId") is not None

                if request.get("keys"):
                    assert item.get("Key") is not None
                    assert item.get("Key") in request["keys"]

        expected_records_in_db = [[StubDataclass(id="saved_from_handler")]]
        for request, expected_records in zip(get_save_to_db_requests(key_str), expected_records_in_db):
            expected_keys = [rec.get_key() for rec in expected_records]

            test_client.post("/tasks/submit", json=request)
            request_object = SubmitRequest(**request)
            response_items = SubmitResponseItem.run_tasks(request_object)
            [Task.wait_for_completion(TaskKey(task_id=response_item.task_run_id)) for response_item in response_items]
            actual_records = list(active(DataSource).load_many(expected_keys))
            assert actual_records == expected_records


if __name__ == "__main__":
    pytest.main([__file__])
