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
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.routers.storage.select_response import SelectResponse
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from stubs.cl.runtime import StubDataclassRecord


def test_method(pytest_default_db):
    """Test coroutine for /storage/select route."""

    # Save test record.
    record = StubDataclassRecord(id=__name__).build()
    DbContext.save_one(record)

    request_obj = SelectRequest(type_=type(record).__name__)
    result = SelectResponse.get_response(request_obj)

    assert isinstance(result, SelectResponse)

    # Check if there are only "schema" and "data".
    assert [x.strip("_") for x in result.model_dump().keys()] == ["schema", "data"]

    # Check result.
    guard = RegressionGuard()
    guard.write(result.model_dump(by_alias=True))
    guard.verify()


def test_api(pytest_default_db):
    """Test REST API for /storage/select route."""
    with QaClient() as test_client:
        # Save test record
        record = StubDataclassRecord(id=__name__).build()
        DbContext.save_one(record)
        request_body = {"Type": "StubDataclassRecord"}

        # Send POST request
        response = test_client.post(
            "/storage/select",
            json=request_body,
        )

        assert response.status_code == 200
        result = response.json()

        # Check result.
        guard = RegressionGuard()
        guard.write(result)
        guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])