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
from cl.runtime.serializers.key_serializer import KeySerializer
from stubs.cl.runtime import StubDataclassRecordKey, StubDataclassCompositeKey

_SAMPLE_TYPES = [
    StubDataclassRecordKey,
    StubDataclassCompositeKey,
]


def test_serialization():
    """Test KeySerializer.serialize method."""

    # Create the serializer
    serializer = KeySerializer().build()

    for sample_type in _SAMPLE_TYPES:

        # Serialize without type information
        obj = sample_type().build()
        untyped_serialized = serializer.serialize(obj)
        untyped_delimited = ";".join(untyped_serialized)

        # Serialize with type information, output should be the same
        typed_serialized = serializer.serialize(obj, (obj.__class__.__name__,))
        assert typed_serialized == untyped_serialized

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(untyped_delimited)

    RegressionGuard().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
