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

import logging
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers
from stubs.cl.runtime import StubIntEnum
from stubs.cl.runtime.records.for_pydantic.stub_pydantic import StubPydantic
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_data import StubPydanticData
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_handlers_key import StubPydanticHandlersKey
from stubs.cl.runtime.records.for_pydantic.stub_pydantic_nested_fields import StubPydanticNestedFields

_logger = logging.getLogger(__name__)


class StubPydanticHandlers(StubPydanticHandlersKey, RecordMixin):
    """Stub class for pydantic-based Record with handlers."""

    def get_key(self) -> KeyMixin:
        return StubPydanticHandlersKey(id=self.id).build()

    @classmethod
    def run_simple_handler(cls) -> None:
        """Simple handler without args and return value."""
        PytestUtil.log_method_info(_logger)

    @classmethod
    def run_handler_with_primitive_args_and_result(cls, str_arg: str, int_arg: int, float_arg: float) -> str:
        """Handler with primitive args and result."""

        PytestUtil.log_method_info(_logger)

        if not isinstance(str_arg, str):
            raise RuntimeError(f"The type of 'str_arg' is '{type(str_arg)}' rather than {typename(str)}.")
        if not isinstance(int_arg, int):
            raise RuntimeError(f"The type of 'int_arg' is '{type(int_arg)}' rather than {typename(int)}.")
        if not isinstance(float_arg, float):
            raise RuntimeError(f"The type of 'float_arg' is '{type(float_arg)}' rather than {typename(float)}.")

        return "Completed"

    @classmethod
    def run_handler_with_mixed_args_and_result(
        cls,
        str_arg: str,
        generic_key_arg: KeyMixin,
        record_arg: StubPydanticNestedFields,
        data_arg: StubPydanticData,
        key_arg: StubPydanticHandlersKey,
        enum_arg: StubIntEnum,
    ):
        """Handler with mixed-type args and result."""

        PytestUtil.log_method_info(_logger)

        if not isinstance(str_arg, str):
            raise RuntimeError(f"The type of 'str_arg' is '{type(str_arg)}' rather than {typename(str)}.")
        if not is_key_type(type(generic_key_arg)):
            raise RuntimeError(f"The type of 'generic_key_arg' is '{type(generic_key_arg)}' rather than Key.")
        if not isinstance(record_arg, StubPydanticNestedFields):
            raise RuntimeError(
                f"The type of 'record_arg' is '{type(record_arg)}' rather than {typename(StubPydanticNestedFields)}"
            )
        if not isinstance(data_arg, StubPydanticData):
            raise RuntimeError(
                f"The type of 'data_arg' is '{type(data_arg)}' rather than {typename(StubPydanticData)}."
            )
        if not isinstance(key_arg, StubPydanticHandlersKey):
            raise RuntimeError(
                f"The type of 'key_arg' is '{type(key_arg)}' rather than {typename(StubPydanticHandlersKey)}."
            )
        if not isinstance(enum_arg, StubIntEnum):
            raise RuntimeError(f"The type of 'enum_arg' is '{type(enum_arg)}' rather than {typename(StubIntEnum)}.")

        return DataSerializers.FOR_UI.serialize(StubPydantic().build())
