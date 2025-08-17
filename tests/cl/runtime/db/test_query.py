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
from cl.runtime.records.conditions import And
from cl.runtime.records.conditions import Exists
from cl.runtime.records.conditions import In
from cl.runtime.records.conditions import Not
from cl.runtime.records.conditions import NotIn
from cl.runtime.records.conditions import Or
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)


def test_str_query(multi_db_fixture):
    """Test query for a string field."""

    # Create test records and query and populate with sample data
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc", obj_str_field=None),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    active(DataSource).insert_many(records)

    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field="def").build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()
    not_in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=NotIn(["def", "xyz"])).build()
    or_query = StubDataclassPrimitiveFieldsQuery(key_str_field=Or("def", "xyz")).build()
    and_query = StubDataclassPrimitiveFieldsQuery(key_str_field=And(Not("def"), Or("def", "xyz"))).build()
    exists_query = StubDataclassPrimitiveFieldsQuery(obj_str_field=Exists(True)).build()
    does_not_exist_query = StubDataclassPrimitiveFieldsQuery(obj_str_field=Exists(False)).build()

    # Load using a query
    to_key_str_field = lambda rec: [x.key_str_field for x in rec]
    assert to_key_str_field(active(DataSource).load_by_query(eq_query)) == ["def"]
    assert to_key_str_field(active(DataSource).load_by_query(in_query)) == ["def", "xyz"]
    assert to_key_str_field(active(DataSource).load_by_query(not_in_query)) == ["abc"]
    # assert to_key_str_field(active(DataSource).load_by_query(or_query)) == ["def", "xyz"]
    # assert to_key_str_field(active(DataSource).load_by_query(and_query)) == ["abc"]
    assert to_key_str_field(active(DataSource).load_by_query(exists_query)) == ["def", "xyz"]
    assert to_key_str_field(active(DataSource).load_by_query(does_not_exist_query)) == ["abc"]


if __name__ == "__main__":
    pytest.main([__file__])
