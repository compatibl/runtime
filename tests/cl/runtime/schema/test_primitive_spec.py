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
import datetime as dt
from types import NoneType
from uuid import UUID
from cl.runtime.schema.primitive_spec import PrimitiveSpec
from cl.runtime.serializers.yaml_serializer import YamlSerializer
from cl.runtime.testing.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubIntEnum

_FROM_CLASS_VALID_CASES = [
    str,
    float,
    bool,
    int,
    (int, "long"),
    dt.date,
    dt.time,
    dt.datetime,
    UUID,
    (UUID, "timestamp"),
    bytes,
]

_FROM_CLASS_EXCEPTION_CASES = [
    NoneType,
    type,
    StubDataclassRecord,
    StubIntEnum,
    (int, "int64"),
    (float, "long"),
]

yaml_serializer = YamlSerializer(omit_type=True).build()


def test_from_class():
    """Test PrimitiveSpec.from_class method."""
    for test_case in _FROM_CLASS_VALID_CASES:

        # Get sample type and subtype (if specified)
        if isinstance(test_case, tuple):
            sample_type, subtype = test_case
        elif isinstance(test_case, type):
            sample_type = test_case
            subtype = None
        else:
            raise RuntimeError("Invalid test case format.")

        # Get enum spec and serialize as YAML
        type_spec = PrimitiveSpec.from_class(sample_type, subtype)
        type_spec_str = yaml_serializer.serialize(type_spec)

        # Record in RegressionGuard
        guard = RegressionGuard(channel=type_spec.type_name)
        guard.write(type_spec_str)
    RegressionGuard().verify_all()


def test_from_class_exceptions():
    """Test PrimitiveSpec.from_class method exceptions."""
    for test_case in _FROM_CLASS_EXCEPTION_CASES:

        # Get sample type and subtype (if specified)
        if isinstance(test_case, tuple):
            sample_type, subtype = test_case
        elif isinstance(test_case, type):
            sample_type = test_case
            subtype = None
        else:
            raise RuntimeError("Invalid test case format.")

        # Check that exception is thrown as expected
        with pytest.raises(Exception):
            PrimitiveSpec.from_class(sample_type, subtype)


if __name__ == "__main__":
    pytest.main([__file__])
