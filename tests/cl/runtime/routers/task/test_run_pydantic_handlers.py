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

from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.routers.task.run_response_util import RunResponseUtil
from cl.runtime.routers.task.run_request import RunRequest
from stubs.cl.runtime.records.for_pydantic.stub_pydantic import StubPydantic

_simple_handler_request = RunRequest(
    type="StubPydanticHandlers",
    method="RunSimpleHandler",
)

_handler_with_primitive_args_and_result_request = RunRequest(
    type="StubPydanticHandlers",
    method="RunHandlerWithPrimitiveArgsAndResult",
    arguments={  # noqa
        "StrArg": "str_value",
        "IntArg": 22,
        "FloatArg": 33.3,
    },
)

_handler_with_mixed_args_and_result_request = RunRequest(
    type="StubPydanticHandlers",
    method="RunHandlerWithMixedArgsAndResult",
    arguments={  # noqa
        "StrArg": "str_value",
        "GenericKeyArg": "StubPydanticKey;stub_generic_key_id1",
        "RecordArg": {"_t": "StubPydanticNestedFields"},
        "DataArg": {"_t": "StubPydanticData"},
        "KeyArg": "stub_key_id1",
        "EnumArg": "EnumValue1",
    },
)

_handler_with_dict_result_request = RunRequest(
    type="StubPydanticHandlers",
    method="RunHandlerWithDictResult",
)


def test_method_simple_handler():
    response = RunResponseUtil.get_response(_simple_handler_request)
    assert response is None


def test_api_simple_method():
    response = PytestUtil.api_task_run(_simple_handler_request)
    assert response is None


def test_method_handler_with_primitive_args_and_result():
    response = RunResponseUtil.get_response(_handler_with_primitive_args_and_result_request)
    assert response == "Completed"


def test_api_handler_with_primitive_args_and_result():
    response = PytestUtil.api_task_run(_handler_with_primitive_args_and_result_request)
    assert response == "Completed"


def test_method_handler_with_mixed_args_and_result():
    response = RunResponseUtil.get_response(_handler_with_mixed_args_and_result_request)
    assert isinstance(response, StubPydantic)


def test_api_handler_with_mixed_args_and_result():
    response = PytestUtil.api_task_run(_handler_with_mixed_args_and_result_request)
    assert response == StubPydantic().build().model_dump(by_alias=True)


def test_method_handler_with_dict_result():
    response = RunResponseUtil.get_response(_handler_with_dict_result_request)
    assert response is not None


def test_api_handler_with_dict_result():
    response = PytestUtil.api_task_run(_handler_with_dict_result_request)
    assert response is not None


if __name__ == "__main__":
    pytest.main([__file__])
