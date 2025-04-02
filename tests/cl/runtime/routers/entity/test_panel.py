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
from cl.runtime.legacy.legacy_response_util import LegacyResponseUtil
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.routers.entity.panel_response_util import PanelResponseUtil
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime import StubDataViewers

_KEY_SERIALIZER = KeySerializers.DELIMITED


def get_requests(key_str: str):
    """Get requests for testing."""
    return [
        # TODO (Roman): Add more test requests.
        {"type_name": "StubDataViewers", "panel_id": "None", "key": key_str},
    ]


def get_expected_results(key_str: str):
    """Get expected_results for testing."""
    return [
        {"ViewOf": None},
    ]


def test_method(pytest_default_db):
    """Test coroutine for /entity/panel route."""

    stub_viewers = StubDataViewers().build()
    key_str = _KEY_SERIALIZER.serialize(stub_viewers.get_key())
    DbContext.save_one(stub_viewers)

    for request, expected_result in zip(get_requests(key_str), get_expected_results(key_str)):
        request_object = PanelRequest(**request)
        result = LegacyResponseUtil.format_panel_response(PanelResponseUtil.get_response(request_object))

        assert isinstance(result, dict)
        assert result == expected_result


def test_api(pytest_default_db):
    """Test REST API for /entity/panel route."""

    stub_viewers = StubDataViewers().build()
    key_str = _KEY_SERIALIZER.serialize(stub_viewers.get_key())
    DbContext.save_one(stub_viewers)

    with QaClient() as test_client:
        for request, expected_result in zip(get_requests(key_str), get_expected_results(key_str)):

            # Get response
            response = test_client.get("/entity/panel", params=request)
            assert response.status_code == 200
            result = response.json()

            # Check result
            assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
