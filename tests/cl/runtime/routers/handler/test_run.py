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

from cl.runtime.routers.handler.run_response_util import RunResponseUtil
from cl.runtime.routers.tasks.submit_request import SubmitRequest

_simple_handler_submit_request = SubmitRequest(
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


def test_method_simple_handler():
    response = RunResponseUtil.get_response(_simple_handler_submit_request)
    assert response == [None]


def test_method_handler_with_primitive_args_and_result():
    response = RunResponseUtil.get_response(_handler_with_primitive_args_and_result_request)
    assert response == ["Completed"]


def test_method_handler_with_mixed_args_and_result():
    response = RunResponseUtil.get_response(_handler_with_mixed_args_and_result_request)
    assert response == [{"Id": "abc", "_t": "StubPydantic"}]
