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
from cl.runtime.services.data_service import DataService
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic


def test_screens(default_db_fixture):

    # Check that screens are empty when db is empty.
    screens = DataService.run_screens()
    assert not screens.get("Result").get("Tables")
    assert not screens.get("Result").get("Types")
    assert not screens.get("Result").get("Filters")

    ds: DataSource = active(DataSource)

    records = [
        StubDataclass(id="stub").build(),
        StubDataclassDerived(id="stub_derived").build(),
        StubDataclassPolymorphic(id="stub_polymorphic").build(),
    ]

    # Save test records
    ds.replace_many(records, commit=True)

    # Check screens data
    screens = DataService.run_screens()
    assert set(x.get("TableName") for x in screens.get("Result").get("Tables")) == {
        "StubDataclassKey",
        "StubDataclassPolymorphicKey",
    }
    assert set(x.get("TypeName") for x in screens.get("Result").get("Types")) == {
        "StubDataclass",
        "StubDataclassDerived",
        "StubDataclassPolymorphic",
    }


def test_select(default_db_fixture):

    # Check that select results are empty when db is empty
    select_table = DataService.run_select_table(table_name="StubDataclassKey")
    assert not select_table.get("Result").get("Data")

    select_type = DataService.run_select_type(type_name="StubDataclass")
    assert not select_type.get("Result").get("Data")

    select_derived_type = DataService.run_select_type(type_name="StubDataclassDerived")
    assert not select_derived_type.get("Result").get("Data")

    ds: DataSource = active(DataSource)

    records = [
        StubDataclass(id="stub_1").build(),
        StubDataclass(id="stub_2").build(),
        StubDataclassDerived(id="stub_derived_1").build(),
        StubDataclassDerived(id="stub_derived_2").build(),
    ]

    # Save test records
    ds.replace_many(records, commit=True)

    # Check select results
    select_table = DataService.run_select_table(table_name="StubDataclassKey")
    assert set(x.get("Id") for x in select_table.get("Result").get("Data")) == {
        "stub_1",
        "stub_2",
        "stub_derived_1",
        "stub_derived_2",
    }

    select_type = DataService.run_select_type(type_name="StubDataclass")
    assert set(x.get("Id") for x in select_type.get("Result").get("Data")) == {
        "stub_1",
        "stub_2",
        "stub_derived_1",
        "stub_derived_2",
    }

    select_derived_type = DataService.run_select_type(type_name="StubDataclassDerived")
    assert set(x.get("Id") for x in select_derived_type.get("Result").get("Data")) == {
        "stub_derived_1",
        "stub_derived_2",
    }

    # TODO (Roman): Implement select by filter


if __name__ == "__main__":
    pytest.main([__file__])
