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
from cl.runtime.routers.handler.run_response_item import RunResponseItem
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from stubs.cl.runtime.records.for_pydantic.stub_pydantic import StubPydantic

_simple_handler_request = SubmitRequest(
    type="StubPydanticHandlers",
    method="SimpleHandler",
)

_handler_with_primitive_args_and_result_request = SubmitRequest(
    type="StubPydanticHandlers",
    method="HandlerWithPrimitiveArgsAndResult",
    arguments={  # noqa
        "StrArg": "str_value",
        "IntArg": 22,
        "FloatArg": 33.3,
    },
)

_handler_with_mixed_args_and_result_request = SubmitRequest(
    type="StubPydanticHandlers",
    method="HandlerWithMixedArgsAndResult",
    arguments={  # noqa
        "StrArg": "str_value",
        "GenericKeyArg": "StubPydanticKey;stub_generic_key_id1",
        "RecordArg": {"_t": "StubPydanticNestedFields"},
        "DataArg": {"_t": "StubPydanticData"},
        "KeyArg": "stub_key_id1",
        "EnumArg": "EnumValue1",
    },
)

_handler_with_dict_result_request = SubmitRequest(
    type="StubPydanticHandlers",
    method="HandlerWithDictResult",
)


def _api_run(run_request: SubmitRequest):
    """Execute run request with test API client."""
    request_body = run_request.model_dump()

    with QaClient() as test_client:
        response = test_client.post("/handler/run", json=request_body)
        assert response.status_code == 200
        return response.json()


def test_method_simple_handler():
    response = RunResponseItem.get_response(_simple_handler_request)
    assert response == [RunResponseItem(result=None)]


def test_api_simple_method():
    response = _api_run(_simple_handler_request)
    assert response == [{"Result": None}]


def test_method_handler_with_primitive_args_and_result():
    response = RunResponseItem.get_response(_handler_with_primitive_args_and_result_request)
    assert response == [RunResponseItem(result="Completed")]


def test_api_handler_with_primitive_args_and_result():
    response = _api_run(_handler_with_primitive_args_and_result_request)
    assert response == [{"Result": "Completed"}]


def test_method_handler_with_mixed_args_and_result():
    response = RunResponseItem.get_response(_handler_with_mixed_args_and_result_request)
    assert len(response) == 1
    assert isinstance(response[0].result, StubPydantic)


def test_api_handler_with_mixed_args_and_result():
    response = _api_run(_handler_with_mixed_args_and_result_request)
    assert len(response) == 1
    assert response[0].get("Result") == StubPydantic().build().model_dump(by_alias=True)


def test_method_handler_with_dict_result():
    response = RunResponseItem.get_response(_handler_with_dict_result_request)
    assert len(response) == 1
    assert response[0].result is not None


def test_api_handler_with_dict_result():
    response = _api_run(_handler_with_dict_result_request)
    assert len(response) == 1
    assert response[0].get("Result") is not None


if __name__ == "__main__":
    pytest.main([__file__])
