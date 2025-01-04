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
import time
from typing import Any
from typing import Iterable
from cl.runtime import Db
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.contexts.env_util import EnvUtil
from cl.runtime.db.sql.sqlite_db import SqliteDb
from cl.runtime.testing.pytest.pytest_fixtures import testing_multi_db
from stubs.cl.runtime import StubDataclassComposite, StubHandlers
from stubs.cl.runtime import StubDataclassDerivedFromDerivedRecord
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerivedRecord
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_key import StubDataclassFinalKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_final_record import StubDataclassFinalRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_final_record import StubDataclassNestedFinalRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased_record import StubDataclassAliasedRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_record import StubDataclassRecord
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned_record import StubDataclassVersionedRecord


def _assert_equals_iterable_without_ordering(iterable: Iterable[Any], other_iterable: Iterable[Any]) -> bool:
    """Checks that two iterables contain the same elements, regardless of order."""

    iterable_as_list = list(iterable) if not isinstance(iterable, list) else iterable
    other_iterable_as_list = list(other_iterable) if not isinstance(other_iterable, list) else other_iterable

    if len(iterable_as_list) != len(other_iterable_as_list):
        raise ValueError(f"Iterables have different length: {len(iterable_as_list)} and {len(other_iterable_as_list)}")

    for item in iterable_as_list:
        if item not in other_iterable_as_list:
            raise ValueError(f"Item {item} contains only in first iterable.")

    return True

def test_record_or_key(testing_multi_db):
    """Test passing record instead of a key."""
    # Create test record and populate with sample data
    record = StubDataclassRecord()
    key = record.get_key()

    # Save a single record
    DbContext.save_many([record])

    # Load using record or key
    loaded_records = tuple(DbContext.load_many(StubDataclassRecord, [record, key, None]))
    assert loaded_records[0] is record  # Same object is returned without lookup
    assert loaded_records[1] == record  # Not the same object but equal
    assert loaded_records[2] is None

    assert DbContext.load_one(StubDataclassRecord, record) is record  # Same object is returned without lookup
    assert DbContext.load_one(StubDataclassRecord, key) == record  # Not the same object but equal


def test_complex_records(testing_multi_db):
    """Test 'save_many' method for various types."""
    samples = [
        StubDataclassRecord(id="abc1"),
        StubDataclassNestedFields(id="abc2"),
        StubDataclassComposite(),
        StubDataclassDerivedRecord(id="abc3"),
        StubDataclassDerivedFromDerivedRecord(id="abc4"),
        StubDataclassOtherDerivedRecord(id="abc5"),
        StubDataclassListFields(id="abc6"),
        StubDataclassOptionalFields(id="abc7"),
        StubDataclassDictFields(id="abc8"),
        StubDataclassDictListFields(id="abc9"),
        StubDataclassListDictFields(id="abc10"),
        StubDataclassPrimitiveFields(key_str_field="abc11"),
        StubDataclassSingleton(),
        StubDataclassAliasedRecord(id="abc12", a=123),
        StubHandlers(stub_id="abc13"),
        StubDataclassRecord(id="abc14"),
        StubDataclassVersionedRecord(id="abc15"),
    ]

    DbContext.save_many(samples)

    sample_keys = [sample.get_key() for sample in samples]
    loaded_records = [DbContext.load_one(type(key), key) for key in sample_keys]

    assert loaded_records == samples


def test_basic_operations(testing_multi_db):
    """Test save/load/delete methods for various types."""
    samples = [
        StubDataclassRecord(id="abc1"),
        StubDataclassNestedFields(id="abc2"),
        StubDataclassComposite(),
        StubDataclassDerivedRecord(id="abc3"),
        StubDataclassDerivedFromDerivedRecord(id="abc4"),
        StubDataclassOtherDerivedRecord(id="abc5"),
        StubDataclassListFields(id="abc6"),
        StubDataclassOptionalFields(id="abc7"),
        StubDataclassDictFields(id="abc8"),
        StubDataclassDictListFields(id="abc9"),
        StubDataclassListDictFields(id="abc10"),
        StubDataclassPrimitiveFields(key_str_field="abc11"),
        StubDataclassSingleton(),
        StubDataclassAliasedRecord(id="abc12", a=123),
        StubHandlers(stub_id="abc13"),
        StubDataclassRecord(id="abc14"),
        StubDataclassVersionedRecord(id="abc15"),
    ]

    sample_keys = [x.get_key() for x in samples]

    # Load from empty tables
    loaded_records = [DbContext.load_one_or_none(type(key), key) for key in sample_keys]
    assert loaded_records == [None] * len(samples)

    # Populate tables
    DbContext.save_many(samples)

    # Load one by one for all keys because each type is different
    loaded_records = [DbContext.load_one(type(key), key) for key in sample_keys]
    assert loaded_records == samples

    # Delete first and last record
    DbContext.delete_many([sample_keys[0], sample_keys[-1]])
    loaded_records = [DbContext.load_one_or_none(type(key), key) for key in sample_keys]
    assert loaded_records == [None, *samples[1:-1], None]

    # Delete all records
    DbContext.delete_many(sample_keys)
    loaded_records = [DbContext.load_one_or_none(type(key), key) for key in sample_keys]
    assert loaded_records == [None] * len(samples)


def test_record_upsert(testing_multi_db):
    """Check that an existing entry is overridden when a new entry with the same key is saved."""
    # Create sample and save
    sample = StubDataclassRecord()
    DbContext.save_one(sample)
    loaded_record = DbContext.load_one(StubDataclassRecord, sample.get_key())
    assert loaded_record == sample

    # create sample with the same key and save
    override_sample = StubDataclassDerivedRecord()
    DbContext.save_one(override_sample)
    loaded_record = DbContext.load_one(StubDataclassDerivedRecord, sample.get_key())
    assert loaded_record == override_sample

    override_sample = StubDataclassDerivedFromDerivedRecord()
    DbContext.save_one(override_sample)
    loaded_record = DbContext.load_one(StubDataclassDerivedFromDerivedRecord, sample.get_key())
    assert loaded_record == override_sample


def test_load_all(testing_multi_db):
    """Test 'load_all' method."""
    base_samples = [
        StubDataclassRecord(id="base1"),
        StubDataclassRecord(id="base2"),
        StubDataclassRecord(id="base3"),
    ]

    derived_samples = [
        StubDataclassDerivedRecord(id="derived1"),
        StubDataclassDerivedFromDerivedRecord(id="derived2"),
    ]

    other_derived_samples = [
        StubDataclassOtherDerivedRecord(id="derived3"),
    ]

    all_samples = base_samples + derived_samples + other_derived_samples

    DbContext.save_many(all_samples)

    loaded_records = DbContext.load_all(StubDataclassRecord)
    assert _assert_equals_iterable_without_ordering(all_samples, loaded_records)

    loaded_records = DbContext.load_all(StubDataclassDerivedRecord)
    assert _assert_equals_iterable_without_ordering(derived_samples, loaded_records)


def test_singleton(testing_multi_db):
    """Test singleton type saving."""
    singleton_sample = StubDataclassSingleton()
    DbContext.save_one(singleton_sample)
    loaded_sample = DbContext.load_one(StubDataclassSingleton, singleton_sample.get_key())
    assert loaded_sample == singleton_sample

    other_singleton_sample = StubDataclassSingleton(str_field="other")
    DbContext.save_one(other_singleton_sample)
    all_records = list(DbContext.load_all(other_singleton_sample.__class__))
    assert len(all_records) == 1
    assert all_records[0] == other_singleton_sample


def test_abstract_key(testing_multi_db):
    """Test final record for which some of the fields are in base record."""
    final_record = StubDataclassFinalRecord(id="a")
    DbContext.save_one(final_record)
    final_key = final_record.get_key()
    load_using_record = DbContext.load_one(type(final_record), final_record)
    load_using_key = DbContext.load_one(type(final_record), final_key)
    assert load_using_record is final_record  # Same object is returned without lookup
    assert load_using_key == final_record  # Not the same object but equal

    nested_record = StubDataclassNestedFinalRecord(id="b")
    nested_record.final_key = StubDataclassFinalKey(id="c")
    nested_record.final_record = StubDataclassFinalRecord(id="d")
    DbContext.save_one(nested_record)
    nested_key = nested_record.get_key()
    load_using_record = DbContext.load_one(type(nested_record), nested_record)
    load_using_key = DbContext.load_one(type(nested_record), nested_key)
    assert load_using_record is nested_record  # Same object is returned without lookup
    assert load_using_key == nested_record  # Not the same object but equal


def test_load_filter(testing_multi_db):
    """Test 'load_filter' method."""
    # Create test record and populate with sample data
    offset = 0
    matching_records = [StubDataclassDerivedRecord(id=str(offset + i), derived_str_field="a") for i in range(2)]
    offset = len(matching_records)
    non_matching_records = [StubDataclassDerivedRecord(id=str(offset + i), derived_str_field="b") for i in range(2)]
    DbContext.save_many(matching_records + non_matching_records)

    filter_obj = StubDataclassDerivedRecord(id=None, derived_str_field="a")
    loaded_records = DbContext.load_filter(StubDataclassDerivedRecord, filter_obj)
    assert len(loaded_records) == len(matching_records)
    assert all(x.derived_str_field == filter_obj.derived_str_field for x in loaded_records)


def test_repeated(testing_multi_db):
    """Test including the same object twice in save many."""
    record = StubDataclassRecord()
    DbContext.save_many([record, record])

    loaded_records = list(DbContext.load_many(StubDataclassRecord, [record.get_key()]))
    assert len(loaded_records) == 1
    assert loaded_records[0] == record


if __name__ == "__main__":
    pytest.main([__file__])
