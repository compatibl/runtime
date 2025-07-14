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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_basic_mongo_db  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_multi_db  # noqa
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.conditions import In
from cl.runtime.records.data_util import DataUtil
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime import StubDataclassTupleFields
from stubs.cl.runtime import StubHandlers
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_aliased import StubDataclassAliased
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_versioned import StubDataclassVersioned

_SAMPLES = [
    sample.build()
    for sample in [
        StubDataclass(id="abc1"),
        StubDataclassNestedFields(id="abc2"),
        StubDataclassComposite(),
        StubDataclassDerived(id="abc3"),
        StubDataclassDoubleDerived(id="abc4"),
        StubDataclassOtherDerived(id="abc5"),
        StubDataclassListFields(id="abc6"),
        StubDataclassTupleFields(id="abc6tuple"),
        StubDataclassOptionalFields(id="abc7"),
        StubDataclassDictFields(id="abc8"),
        StubDataclassDictListFields(id="abc9"),
        StubDataclassListDictFields(id="abc10"),
        StubDataclassPrimitiveFields(key_str_field="abc11"),
        StubDataclassSingleton(),
        StubDataclassAliased(id="abc12", a=123),
        StubHandlers(stub_id="abc13"),
        StubDataclass(id="abc14"),
        StubDataclassVersioned(id="abc15"),
    ]
]


def test_record_or_key(pytest_multi_db):
    """Test passing record instead of a key."""
    # Create test record and populate with sample data
    record = StubDataclass().build()
    key = record.get_key()

    # Save a single record
    DbContext.save_many([record])

    # Load using record or key
    another_record = StubDataclass(id="another").build()
    loaded_records = tuple(DbContext.load_many([another_record, key, None]))
    assert loaded_records[0] is another_record  # Same object is returned without lookup
    assert loaded_records[1] == record  # Not the same object but equal
    assert loaded_records[2] is None

    assert DbContext.load_one(another_record) is another_record  # Same object is returned without lookup
    assert DbContext.load_one(key) == record  # Not the same object but equal


def test_complex_records(pytest_multi_db):
    """Test 'save_many' method for various types."""
    DbContext.save_many(_SAMPLES)

    sample_keys = [sample.get_key() for sample in _SAMPLES]
    loaded_records = [DbContext.load_one(key) for key in sample_keys]

    assert loaded_records == DataUtil.remove_none(_SAMPLES)


def test_basic_operations(pytest_multi_db):
    """Test save/load/delete methods for various types."""
    sample_keys = [x.get_key() for x in _SAMPLES]

    # Load from empty tables
    loaded_records = [DbContext.load_one_or_none(key) for key in sample_keys]
    assert loaded_records == [None] * len(_SAMPLES)

    # Populate tables
    DbContext.save_many(_SAMPLES)

    # Load one by one for all keys because each type is different
    loaded_records = [DbContext.load_one(key) for key in sample_keys]
    assert loaded_records == DataUtil.remove_none(_SAMPLES)

    # Delete first and last record
    DbContext.delete_many([sample_keys[0], sample_keys[-1]])
    loaded_records = [DbContext.load_one_or_none(key) for key in sample_keys]
    assert loaded_records == DataUtil.remove_none([None, *_SAMPLES[1:-1], None])

    # Delete all records
    DbContext.delete_many(sample_keys)
    loaded_records = [DbContext.load_one_or_none(key) for key in sample_keys]
    assert loaded_records == [None] * len(_SAMPLES)


def test_record_upsert(pytest_multi_db):
    """Check that an existing entry is overridden when a new entry with the same key is saved."""
    # Create sample and save
    sample = StubDataclass().build()
    DbContext.save_one(sample)
    loaded_record = DbContext.load_one(sample.get_key())
    assert loaded_record == sample

    # create sample with the same key and save
    override_sample = StubDataclassDerived().build()
    DbContext.save_one(override_sample)
    loaded_record = DbContext.load_one(sample.get_key())
    assert loaded_record == override_sample

    override_sample = StubDataclassDoubleDerived().build()
    DbContext.save_one(override_sample)
    loaded_record = DbContext.load_one(sample.get_key())
    assert loaded_record == override_sample


def test_load_all(pytest_multi_db):
    """Test 'load_all' method."""
    base_samples = [
        sample.build()
        for sample in [
            StubDataclass(id="base1"),
            StubDataclass(id="base2"),
            StubDataclass(id="base3"),
        ]
    ]

    derived_samples = [
        sample.build()
        for sample in [
            StubDataclassDerived(id="derived1"),
            StubDataclassDoubleDerived(id="derived2"),
        ]
    ]

    other_derived_samples = [
        sample.build()
        for sample in [
            StubDataclassOtherDerived(id="derived3"),
        ]
    ]

    all_samples = base_samples + derived_samples + other_derived_samples

    DbContext.save_many(all_samples)

    loaded_records = DbContext.load_all(StubDataclass)
    assert PytestUtil.assert_equals_iterable_without_ordering(all_samples, loaded_records)

    loaded_records = DbContext.load_all(StubDataclassDerived)
    assert PytestUtil.assert_equals_iterable_without_ordering(derived_samples, loaded_records)


def test_singleton(pytest_multi_db):
    """Test singleton type saving."""
    singleton_sample = StubDataclassSingleton().build()
    DbContext.save_one(singleton_sample)
    loaded_sample = DbContext.load_one(
        singleton_sample.get_key(),
        cast_to=StubDataclassSingleton,
    )
    assert loaded_sample == singleton_sample

    other_singleton_sample = StubDataclassSingleton(str_field="other").build()
    DbContext.save_one(other_singleton_sample)
    all_records = list(DbContext.load_all(other_singleton_sample.__class__))
    assert len(all_records) == 1
    assert all_records[0] == other_singleton_sample


def test_repeated(pytest_multi_db):
    """Test including the same object twice in save many."""
    record = StubDataclass().build()
    DbContext.save_many([record, record])

    loaded_records = list(DbContext.load_many([record.get_key()]))
    assert len(loaded_records) == 1
    assert loaded_records[0] == record


def test_load_where(pytest_basic_mongo_db):  # TODO: Use test_multi_db fixture when implemented
    """Test count_where for a string field."""
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc", obj_str_field=None),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    DbContext.save_many(records)

    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field="def").build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()

    # Load using a query
    to_key_str_field = lambda rec: [x.key_str_field for x in rec]
    assert to_key_str_field(DbContext.load_where(eq_query)) == ["def"]
    assert to_key_str_field(DbContext.load_where(in_query)) == ["def", "xyz"]


def test_count_where(pytest_basic_mongo_db):  # TODO: Use test_multi_db fixture when implemented
    """Test count_where for a string field."""
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc", obj_str_field=None),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    DbContext.save_many(records)

    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field="def").build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()

    assert DbContext.count_where(eq_query) == 1
    assert DbContext.count_where(in_query) == 2


if __name__ == "__main__":
    pytest.main([__file__])
