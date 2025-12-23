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
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_response_util import RunResponseUtil
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_class_method_1a_request = RunRequest(
    type="StubHandlers",
    method="run_class_method_1a",
)

_instance_method_1a_request = RunRequest(
    type="StubHandlers",
    key="stub_record",
    method="run_instance_method_1a",
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


def test_method_class_method_1a():
    response = RunResponseUtil.get_response(_class_method_1a_request)
    assert response is None


def test_api_class_method_1a():
    response = PytestUtil.api_task_run(_class_method_1a_request)
    assert response is None

def test_method_instance_method_1a(default_db_fixture):
    _save_record_for_request(_instance_method_1a_request)
    response = RunResponseUtil.get_response(_instance_method_1a_request)
    assert response is None

def test_api_instance_method_1a(default_db_fixture):
    _save_record_for_request(_instance_method_1a_request)
    response = PytestUtil.api_task_run(_instance_method_1a_request)
    assert response is None


if __name__ == "__main__":
    pytest.main([__file__])