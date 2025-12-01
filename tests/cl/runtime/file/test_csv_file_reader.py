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
from cl.runtime.prebuild.csv_file_util import CsvFileUtil
from cl.runtime.qa.qa_util import QaUtil
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassNestedFields


def test_csv_file_reader(default_db_fixture):
    """Test CsvFileUtil class."""

    # Create a new instance of local cache for the test
    env_dir = QaUtil.get_test_dir_from_call_stack()

    records = CsvFileUtil.load_all(dirs=[env_dir], record_types=[StubDataclassDerived])
    active(DataSource).insert_many(records, commit=True)

    records = CsvFileUtil.load_all(dirs=[env_dir], record_types=[StubDataclassNestedFields])
    active(DataSource).insert_many(records, commit=True)

    records = CsvFileUtil.load_all(dirs=[env_dir], record_types=[StubDataclassComposite])
    active(DataSource).insert_many(records, commit=True)

    # Verify
    # TODO: Check count using load_by_type or count method of Db when created
    for i in range(1, 3):
        expected_record = StubDataclassDerived(
            id=f"derived_id_{i}", derived_str_field=f"test_derived_str_field_value_{i}"
        ).build()
        key = StubDataclassKey(id=f"derived_id_{i}").build()
        record = active(DataSource).load_one(key)
        assert record == expected_record

    for i in range(1, 4):
        expected_record = StubDataclassNestedFields().build()
        record = active(DataSource).load_one(expected_record.get_key())
        assert record == expected_record

    for i in range(1, 4):
        expected_record = StubDataclassComposite(
            primitive=f"nested_primitive_{i}",
            embedded_1=StubDataclassKey(id=f"embedded_key_id_{i}a"),
            embedded_2=StubDataclassKey(id=f"embedded_key_id_{i}b"),
        ).build()
        record = active(DataSource).load_one(expected_record.get_key())
        assert record == expected_record


if __name__ == "__main__":
    pytest.main([__file__])
