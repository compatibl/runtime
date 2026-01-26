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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil

requests = [{"type_name": "UiAppState"}]


def test_method():
    """Test coroutine for /schema/type route."""

    for request in requests:
        # Run the coroutine wrapper added by the FastAPI decorator and validate the result
        request_obj = TypeRequest(**request)
        result_dict = TypeResponseUtil.get_type(request_obj)
        RegressionGuard().build().write(result_dict)

    RegressionGuard.verify_all()


def test_api():
    """Test REST API for /schema/type route."""
    with QaClient() as test_client:
        for request in requests:

            # Get response
            response = test_client.get("/schema/type", params=request)
            assert response.status_code == 200
            result = response.json()
            RegressionGuard().build().write(result)

        RegressionGuard.verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
