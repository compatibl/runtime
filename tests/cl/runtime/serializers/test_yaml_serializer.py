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
from cl.runtime.serializers.dict_serializer_2 import DictSerializer2
from cl.runtime.serializers.primitive_serializer import PrimitiveSerializer
from cl.runtime.serializers.yaml_serializer import YamlSerializer
from cl.runtime.testing.regression_guard import RegressionGuard
from stubs.cl.runtime import StubDataclassComposite
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


def test_to_yaml():
    """Test DictSerializer2.to_yaml method."""

    # Create the serializer
    serializer = YamlSerializer().build()

    for sample_type in _SAMPLE_TYPES:

        # Create and serialize to YAML
        obj = sample_type().build()
        obj_yaml = serializer.to_yaml(obj)

        # Write to regression guard
        snake_case_type_name = CaseUtil.pascal_to_snake_case(sample_type.__name__)
        guard = RegressionGuard(channel=snake_case_type_name)
        guard.write(obj_yaml)

    RegressionGuard().verify_all()

def test_from_yaml():
    """Test DictSerializer2.to_yaml method."""

    # Create the serializers
    yaml_serializer = YamlSerializer().build()
    all_string_primitive_serializer = PrimitiveSerializer().build()
    all_string_dict_serializer = DictSerializer2(primitive_serializer=all_string_primitive_serializer).build()

    for sample_type in _SAMPLE_TYPES:

        # Create and serialize to YAML
        obj = sample_type().build()
        obj_yaml = yaml_serializer.to_yaml(obj)

        # Serialize to dict using all_string_dict_serializer flag, all primitive values are strings except None
        all_string_obj_dict = all_string_dict_serializer.to_dict(obj)

        # Deserialize from YAML, when schema is not used all primitive values will be strings
        yaml_dict = yaml_serializer.from_yaml(obj_yaml)

        # Compare the two dictionaries
        assert yaml_dict == all_string_obj_dict


if __name__ == "__main__":
    pytest.main([__file__])
