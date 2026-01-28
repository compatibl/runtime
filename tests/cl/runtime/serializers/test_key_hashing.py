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
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_key_or_record_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.serializers.key_serializers import KeySerializers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_composite_key import StubDataclassCompositeKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_base_key import StubDataclassPolymorphicBaseKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_composite_key import (
    StubDataclassPolymorphicCompositeKey,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_key import StubDataclassPrimitiveFieldsKey

_KEY_SAMPLES = [
    StubDataclassKey().build(),
    StubDataclassCompositeKey().build(),
    StubDataclassPrimitiveFieldsKey().build(),
    StubDataclassPolymorphicKey().build(),
]

_EXCEPTION_SAMPLES = [
    StubDataclassKey(),  # Build is not called, not frozen as a result
]


def test_key_hashing():
    """Test key __hash__ method."""

    guard = RegressionGuard().build()
    for sample in _KEY_SAMPLES:
        hash(sample)
    RegressionGuard.verify_all()


def test_key_hashing_exceptions():
    """Test exception handling in KeySerializer.serialize method."""

    for sample in _EXCEPTION_SAMPLES:
        # Attempt hashing
        with pytest.raises(RuntimeError, match="because it is not frozen"):
            hash(sample)

if __name__ == "__main__":
    pytest.main([__file__])
