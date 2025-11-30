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

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassOtherDerived


def test_get_common_base_record_type(default_db_fixture):
    """Test get common base type function."""

    ds: DataSource = active(DataSource)

    records = [
        StubDataclassDerived(id="stub_derived").build(),
        StubDataclassDoubleDerived(id="stub_double_derived").build(),
    ]

    # Save derived records
    ds.replace_many(records, commit=True)

    # Get the common type of the records stored in the table, or the table's key type if it is empty
    common_base_type = ds.get_common_base_record_type(key_type=StubDataclassKey)
    assert common_base_type == StubDataclassDerived

    # Save other derived record, the common base type becomes StubDataclass
    ds.replace_one(StubDataclassOtherDerived(id="stub_other_derived").build(), commit=True)

    # Get the common type of the records stored in the table, or the table's key type if it is empty
    common_base_type = ds.get_common_base_record_type(key_type=StubDataclassKey)
    assert common_base_type == StubDataclass
