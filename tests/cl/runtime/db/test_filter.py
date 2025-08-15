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

from typing import Sequence
import pytest
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.filter import Filter
from cl.runtime.db.filter_key import FilterKey
from cl.runtime.db.filter_many import FilterMany
from cl.runtime.db.filter_where import FilterWhere
from cl.runtime.records.typename import typename
from stubs.cl.runtime import StubDataclassDerived, StubDataclassKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_query import StubDataclassDerivedQuery


def _test_filter(*, filter: Filter, expected_values: Sequence[str]):
    """Test that the filter can be saved and loaded from storage, and selects the expected values."""

    # Save filter to storage
    active(DataSource).save_one(filter)
    filter_key = filter.get_key()

    # Load the filter from storage
    loaded_filter = active(DataSource).load_one(filter_key)

    # Save test records
    records = [
        StubDataclassDerived(id="1", derived_str_field="abc"),
        StubDataclassDerived(id="2", derived_str_field="def"),
        StubDataclassDerived(id="3", derived_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    active(DataSource).save_many(records)

    # Load records using the filter
    if isinstance(loaded_filter, FilterWhere):
        loaded_records = active(DataSource).load_where(loaded_filter.query, cast_to=StubDataclassDerived)
    elif isinstance(loaded_filter, FilterMany):
        loaded_records = active(DataSource).load_many(loaded_filter.keys, cast_to=StubDataclassDerived)
    else:
        raise RuntimeError(f"Unsupported filter type: {typename(loaded_filter)}")

    # Check if they match the expected values
    assert len(loaded_records) == len(expected_values)
    for record, expected_value in zip(loaded_records, expected_values):
        record.derived_str_field == expected_value


def test_filter_where(multi_db_fixture):
    """Test FilterWhere class."""
    _test_filter(
        filter=FilterWhere(
            filter_id="1",
            key_type_name=typename(StubDataclassKey),
            query = StubDataclassDerivedQuery(
                derived_str_field="def",
            ).build()
        ).build(),
        expected_values=["def"],
    )

@pytest.mark.skip("Requires KeyMixin serialization")
def test_filter_many(multi_db_fixture):
    """Test FilterWhere class."""
    _test_filter(
        filter=FilterMany(
            filter_id="1",
            key_type_name=typename(StubDataclassKey),
            keys = [
                StubDataclassKey(id="1").build(),
                StubDataclassKey(id="2").build(),
            ]
        ).build(),
        expected_values=["abc", "def"],
    )


if __name__ == "__main__":
    pytest.main([__file__])
