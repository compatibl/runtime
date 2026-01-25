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
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.typename import typename
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from stubs.cl.runtime.records.enum.stub_int_enum import StubIntEnum
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass

_FROM_CLASS_VALID_CASES = [
    StubIntEnum,
]

_FROM_CLASS_EXCEPTION_CASES = [
    type,
    StubDataclass,
]


def test_init():
    """Test EnumSpec construction."""
    for test_case in _FROM_CLASS_VALID_CASES:

        # Get enum spec and serialize as YAML
        type_spec = EnumSpec(type_=test_case).build()
        type_spec_str = BootstrapSerializers.YAML.serialize(type_spec)

        # Record in RegressionGuard
        guard = RegressionGuard(prefix=typename(type_spec.type_)).build()
        guard.write(type_spec_str)
    RegressionGuard().build().verify_all()


def test_init_exceptions():
    """Test EnumSpec construction exceptions."""
    for test_case in _FROM_CLASS_EXCEPTION_CASES:
        with pytest.raises(Exception):
            EnumSpec(type_=test_case).build()


if __name__ == "__main__":
    pytest.main([__file__])
