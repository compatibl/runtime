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
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.routers.entity.panel_response_util import PanelResponseUtil
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime import StubDataViewers
from stubs.cl.runtime import StubMediaViewers

_KEY_SERIALIZER = KeySerializers.DELIMITED

_stub_data_viewers = StubDataViewers(stub_id="data_viewers").build()
_stub_media_viewers = StubMediaViewers(stub_id="media_viewers").build()


_data_key = _KEY_SERIALIZER.serialize(_stub_data_viewers.get_key())
_media_key = _KEY_SERIALIZER.serialize(_stub_media_viewers.get_key())

panel_requests = [
    {"type_name": "StubDataViewers", "panel_id": "None", "key": _data_key},
    {"type_name": "StubDataViewers", "panel_id": "Nested Fields", "key": _data_key},
    {"type_name": "StubDataViewers", "panel_id": "Record List", "key": _data_key},
    {"type_name": "StubMediaViewers", "panel_id": "Png", "key": _media_key},
    {"type_name": "StubMediaViewers", "panel_id": "Pdf", "key": _media_key},
    {"type_name": "StubMediaViewers", "panel_id": "Html", "key": _media_key},
    {"type_name": "StubMediaViewers", "panel_id": "Dag", "key": _media_key},
    {"type_name": "StubMediaViewers", "panel_id": "Markdown", "key": _media_key},
]


def test_method(default_db_fixture):
    """Test coroutine for /entity/panel route."""

    DbContext.save_one(_stub_data_viewers)
    DbContext.save_one(_stub_media_viewers)

    for request in panel_requests:
        request_object = PanelRequest(**request)
        result = PanelResponseUtil.get_response(request_object)

        result = BootstrapSerializers.YAML.serialize(result)
        RegressionGuard(channel=request_object.panel_id).write(result)

    RegressionGuard().verify_all()


def test_api(default_db_fixture):
    """Test REST API for /entity/panel route."""

    DbContext.save_one(_stub_data_viewers)
    DbContext.save_one(_stub_media_viewers)

    with QaClient() as test_client:
        for request in panel_requests:

            # Get response
            response = test_client.get("/entity/panel", params=request)
            assert response.status_code == 200
            result = response.json()

            result = BootstrapSerializers.YAML.serialize(result)
            RegressionGuard(channel=request["panel_id"]).write(result)

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
