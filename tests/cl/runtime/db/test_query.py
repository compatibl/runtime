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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_multi_db  # noqa
from cl.runtime.records.conditions import And
from cl.runtime.records.conditions import Eq
from cl.runtime.records.conditions import Exists
from cl.runtime.records.conditions import In
from cl.runtime.records.conditions import Not
from cl.runtime.records.conditions import Or
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields_query import StubDataclassNestedFieldsQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)


@pytest.mark.skip("Query support implementation in progress.")
def test_str_query(pytest_multi_db):
    """Test query with primitive fields."""

    # Create test records and query and populate with sample data
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc"),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    DbContext.save_many(records)

    exists_query = StubDataclassPrimitiveFieldsQuery(key_str_field=Exists(True)).build()
    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field=Eq("def")).build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()
    or_query = StubDataclassPrimitiveFieldsQuery(key_str_field=Or(Eq("def"), Eq("xyz"))).build()
    and_query = StubDataclassPrimitiveFieldsQuery(key_str_field=And(Not(Eq("def")), Not(Eq("xyz")))).build()

    # Load using record or key
    to_key_str_field = lambda rec: [x.key_str_field for x in rec]
    assert to_key_str_field(DbContext.query(StubDataclassPrimitiveFields, exists_query)) == ["abc", "def", "xyz"]
    assert to_key_str_field(DbContext.query(StubDataclassPrimitiveFields, eq_query)) == ["def"]
    assert to_key_str_field(DbContext.query(StubDataclassPrimitiveFields, in_query)) == ["def", "xyz"]
    assert to_key_str_field(DbContext.query(StubDataclassPrimitiveFields, or_query)) == ["def", "xyz"]
    assert to_key_str_field(DbContext.query(StubDataclassPrimitiveFields, and_query)) == ["abc"]


@pytest.mark.skip("Query support implementation in progress.")
def test_key_query(pytest_multi_db):
    """Test query with nested fields."""

    # Create test records and query and populate with sample data
    records = [
        StubDataclassNestedFields(key_field=StubDataclassRecordKey(id="abc")),
        StubDataclassNestedFields(key_field=StubDataclassRecordKey(id="def")),
        StubDataclassNestedFields(key_field=StubDataclassRecordKey(id="xyz")),
    ]
    records = [x.build() for x in records]
    DbContext.save_many(records)

    # Create queries
    key_abc = StubDataclassRecordKey(id="abc")
    key_def = StubDataclassRecordKey(id="def")
    key_xyz = StubDataclassRecordKey(id="xyz")
    exists_query = StubDataclassNestedFieldsQuery(key_field=Exists(True)).build()
    eq_query = StubDataclassNestedFieldsQuery(key_field=Eq(key_def)).build()
    in_query = StubDataclassNestedFieldsQuery(key_field=In([key_def, key_xyz])).build()
    or_query = StubDataclassNestedFieldsQuery(key_field=Or(Eq(key_def), Eq(key_xyz))).build()
    and_query = StubDataclassNestedFieldsQuery(key_field=And(Not(Eq(key_def)), Not(Eq(key_xyz)))).build()

    # Load using record or key
    to_keys = lambda rec: [x.get_key() for x in rec]
    assert to_keys(DbContext.query(StubDataclassNestedFields, exists_query)) == [key_abc, key_def, key_xyz]
    assert to_keys(DbContext.query(StubDataclassNestedFields, eq_query)) == [key_def]
    assert to_keys(DbContext.query(StubDataclassNestedFields, in_query)) == [key_def, key_xyz]
    assert to_keys(DbContext.query(StubDataclassNestedFields, or_query)) == [key_def, key_xyz]
    assert to_keys(DbContext.query(StubDataclassNestedFields, and_query)) == [key_abc]


if __name__ == "__main__":
    pytest.main([__file__])
