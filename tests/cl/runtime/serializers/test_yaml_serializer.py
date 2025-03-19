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
from unicodedata import bidirectional

from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.primitive.primitive_serializers import PrimitiveSerializers
from cl.runtime.records.protocols import SEQUENCE_CLASSES, MAPPING_CLASSES
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2
from cl.runtime.serializers.yaml_serializer import YamlSerializer
from cl.runtime.testing.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassComposite, StubDataclassDerivedData
from stubs.cl.runtime import StubDataclassDerivedFromDerivedRecord
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerivedRecord
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime import StubDataclassTupleFields

_SAMPLE_TYPES = [
    StubDataclassRecord,
    StubDataclassNestedFields,
    StubDataclassComposite,
    StubDataclassDerivedRecord,
    StubDataclassDerivedFromDerivedRecord,
    StubDataclassOtherDerivedRecord,
    StubDataclassListFields,
    StubDataclassOptionalFields,
    StubDataclassDictFields,
    StubDataclassDictListFields,
    StubDataclassListDictFields,
    StubDataclassPrimitiveFields,
    StubDataclassSingleton,
    StubDataclassTupleFields,
]


# TODO: Move to a dedicated utility class
def approx(data, abs_tol=1e-6, rel_tol=1e-6):
    """Recursively apply pytest.approx to all floats in a nested structure."""
    if isinstance(data, float):
        # Apply rounding to float values
        return pytest.approx(data, abs=abs_tol, rel=rel_tol)
    elif isinstance(data, SEQUENCE_CLASSES):
        # Recreate the same sequence type with pytest.approx for float
        sequence_type = data.__class__
        return sequence_type(approx(item, abs_tol, rel_tol) for item in data)
    elif isinstance(data, MAPPING_CLASSES):
        # Recreate the same mapping type with pytest.approx for float
        mapping_type = data.__class__
        return mapping_type((key, approx(value, abs_tol, rel_tol)) for key, value in data.items())
    return data


def test_to_yaml():
    """Test DictSerializer2.to_yaml method."""

    # Create the serializer
    serializer = YamlSerializer(bidirectional=True).build()

    for sample_type in _SAMPLE_TYPES:

        # Create and serialize to YAML
        obj = sample_type().build()
        obj_yaml = serializer.serialize(obj)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(obj_yaml)

    RegressionGuard().verify_all()


def test_from_yaml():
    """Test DictSerializer2.to_yaml method."""

    # Create the serializers
    yaml_serializer = YamlSerializer(bidirectional=True).build()
    passthrough_serializer = DictSerializer2(bidirectional=True).build()

    for sample_type in _SAMPLE_TYPES:

        # Create and serialize to YAML
        obj = sample_type().build()
        serialized = yaml_serializer.serialize(obj)

        # Serialize to dict using all_string_dict_serializer flag, all primitive values are strings except None
        # all_string_obj_dict = all_string_dict_serializer.serialize(obj)

        # Deserialize from YAML, when schema is not used all primitive values will be strings
        deserialized = yaml_serializer.deserialize(serialized)

        # Use passthrough serializer to convert both to dicts
        obj_dict = passthrough_serializer.serialize(obj)
        deserialized_dict = passthrough_serializer.serialize(deserialized)

        # Compare with floating point tolerance
        assert deserialized_dict == approx(obj_dict)


if __name__ == "__main__":
    pytest.main([__file__])
