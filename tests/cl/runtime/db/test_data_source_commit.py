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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_key import StubDataclassKey


def test_commit(multi_db_fixture):
    """Test commit method."""
    sample = StubDataclass().build()
    ds = active(DataSource)
    ds.insert_one(sample, commit=False)
    assert ds.load_one_or_none(sample.get_key()) is None
    ds.commit()
    assert ds.load_one_or_none(sample.get_key()) == sample


def test_rollback(multi_db_fixture):
    """Test rollback method."""
    sample_a = StubDataclass(id="a").build()
    sample_b = StubDataclass(id="b").build()
    ds = active(DataSource)
    ds.insert_one(sample_a, commit=False)
    assert ds.load_one_or_none(sample_a.get_key()) is None
    ds.rollback()
    ds.insert_one(sample_b, commit=False)
    ds.commit()
    assert ds.load_one_or_none(sample_a.get_key()) is None
    assert ds.load_one_or_none(sample_b.get_key()) == sample_b


def test_pre_commit_exception(default_db_fixture):
    """Test an exception before commit is called."""
    try:
        with activate(active(DataSource)) as ds:
            # Not a key, will raise
            ds.delete_one(StubDataclass().build(), commit=False)
    except RuntimeError as e:
        # Do not rethrow
        pass
    # Ensure pending operations were cleared
    assert not ds._has_pending_operations()


def test_commit_collisions(default_db_fixture):
    """Test commit method."""
    sample_1 = StubDataclass().build()
    sample_2 = StubDataclass().build()
    sample_key_1 = StubDataclassKey().build()
    sample_key_2 = StubDataclassKey().build()

    match_str = "present more than once"
    with pytest.raises(RuntimeError, match=match_str):
        ds = active(DataSource)
        ds.insert_one(sample_1, commit=False)
        ds.insert_one(sample_2, commit=False)
        ds.insert_one(sample_1, commit=False)
        ds.commit()
    with pytest.raises(RuntimeError, match=match_str):
        ds = active(DataSource)
        ds.replace_one(sample_1, commit=False)
        ds.replace_one(sample_1, commit=False)
        ds.replace_one(sample_2, commit=False)
        ds.commit()
    with pytest.raises(RuntimeError, match=match_str):
        ds = active(DataSource)
        ds.insert_one(sample_1, commit=False)
        ds.insert_one(sample_2, commit=False)
        ds.replace_one(sample_1, commit=False)
        ds.commit()
    with pytest.raises(RuntimeError, match=match_str):
        ds = active(DataSource)
        ds.insert_one(sample_1, commit=False)
        ds.insert_one(sample_2, commit=False)
        ds.delete_one(sample_key_1, commit=False)
        ds.commit()
    with pytest.raises(RuntimeError, match=match_str):
        ds = active(DataSource)
        ds.delete_one(sample_key_1, commit=False)
        ds.delete_one(sample_key_2, commit=False)
        ds.commit()


if __name__ == "__main__":
    pytest.main([__file__])
