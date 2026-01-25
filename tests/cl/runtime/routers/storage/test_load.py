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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.typename import typename
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.load_response import LoadResponse
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


def test_method(default_db_fixture):
    """Test coroutine for /storage/load route."""

    # Save test record.
    record = StubDataclass(id=__name__).build()
    active(DataSource).replace_one(record, commit=True)

    # Run the coroutine wrapper added by the FastAPI decorator and get the result.
    load_request = LoadRequest(load_keys=[KeyRequestItem(key=record.id, type=typename(StubDataclass))])
    result = LoadResponse.get_response(load_request)

    # Check if the result is a LoadResponse instance.
    assert isinstance(result, LoadResponse)

    # Check if there are only "schema" and "data".
    assert [x.strip("_") for x in dict(result).keys()] == ["schema", "data"]

    # Check result.
    guard = RegressionGuard().build()
    guard.write(result.model_dump(by_alias=True))
    guard.verify()


def test_api(default_db_fixture):
    """Test REST API for /storage/load route."""

    with QaClient() as test_client:
        # Save test record.
        record = StubDataclass(id=__name__).build()
        active(DataSource).replace_one(record, commit=True)

        # Request body.
        request_body = [KeyRequestItem(key=record.id, type=typename(StubDataclass)).model_dump()]

        # Get response.
        response = test_client.post("/storage/load", json=request_body)
        assert response.status_code == 200
        result = response.json()

        # Check result.
        guard = RegressionGuard().build()
        guard.write(result)
        guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
