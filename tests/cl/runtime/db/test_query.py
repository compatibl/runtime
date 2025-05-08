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
from cl.runtime.records.for_dataclasses.string_query import StringQuery
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import StubDataclassPrimitiveFieldsQuery


def test_primitive_fields(pytest_multi_db):
    """Test query with primitive fields."""

    # Create test records and query and populate with sample data
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc"),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    query = StubDataclassPrimitiveFieldsQuery(key_str_field=StringQuery(eq="def")).build()

    # Save a single record
    DbContext.save_many(records)

    # Load using record or key
    queried_records = DbContext.query(StubDataclassPrimitiveFields, query)
    assert len(queried_records) == 1
    assert queried_records[0].key_str_field == "def"


if __name__ == "__main__":
    pytest.main([__file__])
