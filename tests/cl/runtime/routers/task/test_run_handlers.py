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
from cl.runtime.records.typename import typename
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_response_util import RunResponseUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime import StubHandlers, StubDataclass

_class_method_1a_request = RunRequest(
    type=typename(StubHandlers),
    method="run_class_method_1a",
)

_instance_method_1a_request = RunRequest(
    type=typename(StubHandlers),
    key="stub_record",
    method="run_instance_method_1a",
)

_method_persist_record_request = RunRequest(
    type=typename(StubHandlers),
    key="stub_record",
    method="run_method_persist_record",
    arguments={"Record": {"Id": "record_saved_in_handler", "_t": typename(StubDataclass)}},
)

def _save_record_for_request(request: RunRequest):
    """Save a record if request is instance method."""
    # Do nothing if request.key is None
    if request.key is None:
        return

    # Create Record using Key fields
    record_type = TypeInfo.from_type_name(request.type)
    key_type = record_type.get_key_type()
    key_type_hint = TypeHint.for_type(key_type)

    key = KeySerializers.DELIMITED.deserialize(request.key, type_hint=key_type_hint)
    data_dict = DataSerializers.DEFAULT.serialize(key)
    data_dict["_type"] = request.type
    record = DataSerializers.DEFAULT.deserialize(data_dict)

    # Save record
    active(DataSource).replace_one(record, commit=True)


def test_method_class_method_1a(default_db_fixture, event_broker_fixture):
    response = RunResponseUtil.get_response(_class_method_1a_request)
    assert response is None

def test_api_class_method_1a(default_db_fixture, event_broker_fixture):
    response = PytestUtil.api_task_run(_class_method_1a_request)
    assert response is None

def test_method_instance_method_1a(default_db_fixture, event_broker_fixture):
    _save_record_for_request(_instance_method_1a_request)
    response = RunResponseUtil.get_response(_instance_method_1a_request)
    assert response is None

def test_api_instance_method_1a(default_db_fixture, event_broker_fixture):
    _save_record_for_request(_instance_method_1a_request)
    response = PytestUtil.api_task_run(_instance_method_1a_request)
    assert response is None

def test_method_persist_record(default_db_fixture, event_broker_fixture):
    _save_record_for_request(_method_persist_record_request)
    response = RunResponseUtil.get_response(_method_persist_record_request)
    assert response is None

    # Check that record successfully saved from handler
    record_arg = DataSerializers.FOR_UI.deserialize(_method_persist_record_request.arguments["Record"])
    record_saved_in_handler = active(DataSource).load_one_or_none(record_arg.get_key())
    assert record_saved_in_handler is not None

def test_api_persist_record(default_db_fixture, event_broker_fixture):
    _save_record_for_request(_method_persist_record_request)
    response = PytestUtil.api_task_run(_method_persist_record_request)
    assert response is None

    # Check that record successfully saved from handler
    record_arg = DataSerializers.FOR_UI.deserialize(_method_persist_record_request.arguments["Record"])
    record_saved_in_handler = active(DataSource).load_one_or_none(record_arg.get_key())
    assert record_saved_in_handler is not None


if __name__ == "__main__":
    pytest.main([__file__])
