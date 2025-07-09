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
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.qa.pytest.pytest_fixtures import patch_uuid_conversion  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_basic_mongo_db  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_multi_db  # noqa
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_query import StubDataclassPolymorphicQuery


def test_load(pytest_basic_mongo_db):  # TODO: Switch to pytest_multi_db after load_where is completed for all DBs
    """Test load methods."""

    table_field = "StubPolymorphicTable"
    key_field = "stub_key_field"
    record_field = "stub_record_field"

    # Create and save a record derived from a generic base
    record = StubDataclassPolymorphic(
        table_field=table_field,
        key_field=key_field,
        record_field=record_field,
    ).build()
    DbContext.save_one(record)

    # Test get_key
    key = StubDataclassPolymorphicKey(table_field=table_field, key_field=key_field).build()
    assert record.get_key() == key

    # Test serialize_key
    serialized_key = (table_field, key_field)
    assert key.serialize_key() == serialized_key

    # Get record from DB using key
    loaded_record = DbContext.load_one(key, cast_to=StubDataclassPolymorphic)
    assert loaded_record == record

    # Test load_where method
    query = StubDataclassPolymorphicQuery(
        table_field=table_field,
        record_field=record_field,
    ).build()
    loaded_where = DbContext.load_where(query, cast_to=StubDataclassPolymorphic)


if __name__ == "__main__":
    pytest.main([__file__])
