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
from typing import Sequence
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.filter import Filter
from cl.runtime.db.filter_by_query import FilterByQuery
from cl.runtime.db.filter_by_type import FilterByType
from cl.runtime.db.filter_many import FilterMany
from cl.runtime.records.typename import typename
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassOtherDerived
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
        StubDataclassOtherDerived(id="4", other_derived="uvw"),
    ]
    records = [x.build() for x in records]
    active(DataSource).save_many(records)

    # Load records using the filter
    loaded_records = active(DataSource).load_by_filter(loaded_filter, cast_to=StubDataclassDerived)

    # Check if they match the expected values
    assert len(loaded_records) == len(expected_values)
    for record, expected_value in zip(loaded_records, expected_values):
        assert record.id == expected_value


def test_filter_by_query(multi_db_fixture):
    """Test FilterByQuery class."""
    _test_filter(
        filter=FilterByQuery(
            filter_id="1",
            key_type_name=typename(StubDataclassKey),
            query=StubDataclassDerivedQuery(
                derived_str_field="def",
            ).build(),
        ).build(),
        expected_values=["2"],
    )


def test_filter_by_type(multi_db_fixture):
    """Test FilterByQuery class."""
    _test_filter(
        filter=FilterByType(
            record_type_name="StubDataclassDerived",
        ).build(),
        expected_values=["1", "2", "3"],
    )
    _test_filter(
        filter=FilterByType(
            record_type_name="StubDataclassOtherDerived",
        ).build(),
        expected_values=["4"],
    )


@pytest.mark.skip("Requires KeyMixin serialization")
def test_filter_by_keys(multi_db_fixture):
    """Test FilterByQuery class."""
    _test_filter(
        filter=FilterMany(
            filter_id="1",
            key_type_name=typename(StubDataclassKey),
            keys=[
                StubDataclassKey(id="1").build(),
                StubDataclassKey(id="2").build(),
            ],
        ).build(),
        expected_values=["1", "2"],
    )


if __name__ == "__main__":
    pytest.main([__file__])
