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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_concrete_record import StubDataclassConcreteRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_1 import StubDataclassGenericArg1
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_record_key import StubDataclassGenericRecordKey


def test_concrete_record(pytest_default_db):
    """Test StubDataclassConcreteRecord."""

    # Create and save a record derived from a generic base
    record = StubDataclassConcreteRecord(
        key_field=StubDataclassRecordKey(),
        record_field=StubDataclassGenericArg1(),
    ).build()
    DbContext.save_one(record)

    # Test key
    key = StubDataclassGenericRecordKey(key_field=StubDataclassRecordKey()).build()
    assert key == record.get_key()

    # Get record from DB using key
    loaded_record = DbContext.load_one(StubDataclassConcreteRecord, key)
    assert loaded_record == record

if __name__ == "__main__":
    pytest.main([__file__])
