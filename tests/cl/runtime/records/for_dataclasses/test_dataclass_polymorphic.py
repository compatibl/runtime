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
from typing import Generic, TypeVar

import pytest
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey

def test_smoke(pytest_default_db):
    """Smoke test."""

    # Create and save a record derived from a generic base
    record = StubDataclassPolymorphic(
        table_field="stub_table_field",
        key_field="stub_key_field",
        record_field="stub_record_field",
    ).build()
    DbContext.save_one(record)

    # Test key
    key = StubDataclassPolymorphicKey(table_field="stub_table_field", key_field="stub_key_field").build()
    assert key == record.get_key()

    # Get record from DB using key
    loaded_record = DbContext.load_one(StubDataclassPolymorphic, key)
    assert loaded_record == record


if __name__ == "__main__":
    pytest.main([__file__])
