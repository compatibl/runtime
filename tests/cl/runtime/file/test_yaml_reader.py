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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.yaml_reader import YamlReader
from cl.runtime.qa.qa_util import QaUtil
from stubs.cl.runtime import StubDataclassComposite, StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassNestedFields


TEST_INPUTS = [
    "StubDataclass.yaml",
    "StubDataclassDerived.yaml",
    "StubDataclassNestedFields.yaml",
    "StubDataclassComposite.yaml",
    "StubDataclassSingle.yaml",
]

EXPECTED_OUTPUTS = [
    StubDataclassDerived(
        id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}"
    ) for i in range(1, 3)
] + [
    StubDataclassComposite(
        primitive=f"nested_primitive_{i}",
        embedded_1=StubDataclassKey(id=f"embedded_key_id_{i}a"),
        embedded_2=StubDataclassKey(id=f"embedded_key_id_{i}b"),
    ) for i in range(1, 4)
] + [
    StubDataclassNestedFields(),
    StubDataclassDerived(
        id=f"with_type",
        derived_str_field=f"explicit_type_value"
    ),
    StubDataclass(
        id=f"without_type",
    ),
    StubDataclass(
        id=f"single_record",
    )
]


def test_yaml_reader(default_db_fixture):
    """Test YamlReader class."""

    # Arrange: create a new instance of local cache for the test
    env_dir = QaUtil.get_test_dir_from_call_stack()

    # Act: read each test input file in the env_dir and load data into the local cache
    yaml_reader = YamlReader().build()
    records = yaml_reader.load_all(dirs=[env_dir], ext="yaml")
    active(DataSource).insert_many(records, commit=True)

    # Assert: verify the data loaded into the local cache
    for expected_record in EXPECTED_OUTPUTS:
        expected_record = expected_record.build()
        record = active(DataSource).load_one(expected_record.get_key())
        assert record == expected_record


if __name__ == "__main__":
    pytest.main([__file__])

