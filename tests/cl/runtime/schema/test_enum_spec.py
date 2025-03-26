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
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.serializers.yaml_serializers import YamlSerializers
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubIntEnum

_FROM_CLASS_VALID_CASES = [
    StubIntEnum,
]

_FROM_CLASS_EXCEPTION_CASES = [
    type,
    StubDataclassRecord,
]


def test_from_class():
    """Test EnumSpec.from_class method."""
    for test_case in _FROM_CLASS_VALID_CASES:

        # Get enum spec and serialize as YAML
        type_spec = EnumSpec.from_class(test_case)
        type_spec_str = YamlSerializers.REPORTING.serialize(type_spec)

        # Record in RegressionGuard
        guard = RegressionGuard(channel=type_spec.type_name)
        guard.write(type_spec_str)
    RegressionGuard().verify_all()


def test_from_class_exceptions():
    """Test EnumSpec.from_class method exceptions."""
    for test_case in _FROM_CLASS_EXCEPTION_CASES:
        with pytest.raises(Exception):
            EnumSpec.from_class(test_case)


if __name__ == "__main__":
    pytest.main([__file__])
