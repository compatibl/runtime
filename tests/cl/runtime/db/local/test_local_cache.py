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
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.local.local_cache import LocalCache
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


def test_smoke():
    """Smoke test."""

    with activate(DataSource(db=LocalCache()).build()):

        # Create test record and populate with sample data
        record = StubDataclass().build()
        key = record.get_key()

        # Save a single record
        active(DataSource).insert_many([record])

        loaded_records = active(DataSource).load_many_or_none([record, key, None])
        assert loaded_records[0] is record  # Same object is returned without lookup
        assert loaded_records[1] is record  # In case of local cache only, also the same object
        assert loaded_records[2] is None


if __name__ == "__main__":
    pytest.main([__file__])
