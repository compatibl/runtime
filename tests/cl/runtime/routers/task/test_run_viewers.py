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
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.typename import typename
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_response_util import RunResponseUtil
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
    RunRequest(type=typename(StubDataViewers), method="ViewNone", key=_data_key),
    RunRequest(type=typename(StubDataViewers), method="ViewNestedFields", key=_data_key),
    RunRequest(type=typename(StubDataViewers), method="ViewRecordList", key=_data_key),
    RunRequest(type=typename(StubDataViewers), method="ViewPng", key=_media_key),
    RunRequest(type=typename(StubDataViewers), method="ViewPdf", key=_media_key),
    RunRequest(type=typename(StubDataViewers), method="ViewHtml", key=_media_key),
    RunRequest(type=typename(StubDataViewers), method="ViewDag", key=_media_key),
    RunRequest(type=typename(StubDataViewers), method="ViewMarkdown", key=_media_key),
]

def test_method(default_db_fixture, event_broker_fixture):
    active(DataSource).replace_one(_stub_data_viewers, commit=True)
    active(DataSource).replace_one(_stub_media_viewers, commit=True)

    for request in panel_requests:
        response = RunResponseUtil.get_response(request)

        result = BootstrapSerializers.YAML.serialize(response)
        RegressionGuard(channel=request.method).write(result)

    RegressionGuard().verify_all()


def test_api(default_db_fixture, event_broker_fixture):
    active(DataSource).replace_one(_stub_data_viewers, commit=True)
    active(DataSource).replace_one(_stub_media_viewers, commit=True)

    for request in panel_requests:
        response = PytestUtil.api_task_run(request)

        result = BootstrapSerializers.YAML.serialize(response)
        RegressionGuard(channel=request.method).write(result)

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
