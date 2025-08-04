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
from cl.runtime.contexts.data_context import DataContext
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dynamic import StubDataclassDynamic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dynamic_key import StubDataclassDynamicKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dynamic_query import StubDataclassDynamicQuery


def test_load(multi_db_fixture):
    """Test load methods."""

    table_field = "StubPolymorphicTable"
    key_field = "stub_key_field"
    record_field = "stub_record_field"

    # Create and save a record derived from a generic base
    record = StubDataclassDynamic(
        table_field=table_field,
        key_field=key_field,
        record_field=record_field,
    ).build()
    DataContext.save_one(record)

    # Test get_key
    key = StubDataclassDynamicKey(table_field=table_field, key_field=key_field).build()
    assert record.get_key() == key

    # Get record from DB using key
    loaded_record = DataContext.load_one(key, cast_to=StubDataclassDynamic)
    assert loaded_record == record

    # Test load_where method
    query = StubDataclassDynamicQuery(
        table_field=table_field,
        record_field=record_field,
    ).build()
    loaded_where = DataContext.load_where(query, cast_to=StubDataclassDynamic)


def test_count_where(multi_db_fixture):
    """Test count_where method."""
    table_field = "StubPolymorphicTable"
    key_field = "stub_key_field"
    record_field = "stub_record_field"

    # Create and save a record derived from a generic base
    record = StubDataclassDynamic(
        table_field=table_field,
        key_field=key_field,
        record_field=record_field,
    ).build()
    DataContext.save_one(record)

    # Create the same query as in test_load
    query = StubDataclassDynamicQuery(
        table_field=table_field,
        record_field=record_field,
    ).build()
    count = DataContext.count_where(query, filter_to=StubDataclassDynamic)
    assert count == 1


if __name__ == "__main__":
    pytest.main([__file__])
