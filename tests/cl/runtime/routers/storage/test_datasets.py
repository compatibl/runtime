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
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.storage.datasets_request import DatasetsRequest
from cl.runtime.routers.storage.datasets_response_item import DatasetsResponseItem

requests = [{"type_name": "StubClass"}]

expected_result = [
    {
        "Name": None,
        "Parent": None,
    }
]


def test_method():
    """Test coroutine for /storage/datasets route."""

    for request in requests:
        # Run the coroutine wrapper added by the FastAPI decorator and get the result.
        request_obj = DatasetsRequest(**request)
        result = DatasetsResponseItem.get_datasets(request_obj)

        # Check if the result is a list.
        assert isinstance(result, list)

        # Check if each item in the result is a DatasetsResponseItem instance.
        assert all(isinstance(x, DatasetsResponseItem) for x in result)

        # Check if each item in the result is a valid DatasetsResponseItem instance.
        assert result == [DatasetsResponseItem(**x) for x in expected_result]


def test_api():
    """Test REST API for /storage/datasets route."""
    with QaClient() as test_client:
        for request in requests:
            # Get response.
            response = test_client.get("/storage/datasets", params=request)
            assert response.status_code == 200
            result = response.json()

            # Check result.
            assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
