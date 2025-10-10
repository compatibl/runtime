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
from cl.runtime.contexts.context_manager import active, activate
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.db.tenant_key import TenantKey
from cl.runtime.events.event import Event
from cl.runtime.events.event_kind import EventKind
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.builder_checks import BuilderChecks
from cl.runtime.records.conditions import In
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassKey
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
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_derived_query import StubDataclassDerivedQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_numpy_fields import StubDataclassNumpyFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic import StubDataclassPolymorphic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_composite import (
    StubDataclassPolymorphicComposite,
)
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_polymorphic_key import StubDataclassPolymorphicKey
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
        StubDataclassPolymorphic(id="abc16"),
        StubDataclassPolymorphic(
            id="abc17",
            base_key_field=StubDataclassPolymorphicKey(),
            root_key_field=StubDataclassPolymorphicKey(),
            record_as_base_key_field=StubDataclassPolymorphic(),
            record_as_root_key_field=StubDataclassPolymorphic(),
        ),
        StubDataclassPolymorphicComposite(
            base_key_field=StubDataclassPolymorphicKey(id="abc18"),
            root_key_field=StubDataclassPolymorphicKey(id="abc18"),
        ),
        StubDataclassNumpyFields(),
    ]
]


def test_key_or_record(multi_db_fixture):
    """Test passing record instead of a key."""
    # Create test record and populate with sample data
    record = StubDataclass().build()
    key = record.get_key()

    # Save a single record
    active(DataSource).insert_one(record, commit=True)

    # Load using record or key
    another_record = StubDataclass(id="another").build()
    loaded_records = tuple(active(DataSource).load_many_or_none([another_record, key, None]))
    assert loaded_records[0] is another_record  # Same object is returned without lookup
    assert loaded_records[1] == record  # Not the same object but equal
    assert loaded_records[2] is None

    assert active(DataSource).load_one(another_record) is another_record  # Same object is returned without lookup
    assert active(DataSource).load_one(key) == record  # Not the same object but equal


def test_insert_many(multi_db_fixture):
    """Test 'insert_many' method for various types."""
    active(DataSource).insert_many(_SAMPLES, commit=True)

    sample_keys = [sample.get_key() for sample in _SAMPLES]
    loaded_records = [active(DataSource).load_one(key) for key in sample_keys]

    assert BuilderChecks.is_equal(loaded_records, _SAMPLES)


def test_replace_many(multi_db_fixture):
    """Test 'insert_many' method for various types."""
    active(DataSource).insert_many(_SAMPLES, commit=True)

    sample_keys = [sample.get_key() for sample in _SAMPLES]
    loaded_records = [active(DataSource).load_one(key) for key in sample_keys]
    assert BuilderChecks.is_equal(loaded_records, _SAMPLES)

    active(DataSource).replace_many(_SAMPLES, commit=True)
    loaded_records = [active(DataSource).load_one(key) for key in sample_keys]
    assert BuilderChecks.is_equal(loaded_records, _SAMPLES)


def test_basic_operations(multi_db_fixture):
    """Test save/load/delete methods for various types."""

    sample_keys = [x.get_key() for x in _SAMPLES]

    # Load from empty tables
    loaded_records = [active(DataSource).load_one_or_none(key) for key in sample_keys]
    assert loaded_records == [None] * len(_SAMPLES)

    # Populate tables
    active(DataSource).insert_many(_SAMPLES, commit=True)

    # Load one by one for all keys because each type is different
    loaded_records = [active(DataSource).load_one(key) for key in sample_keys]
    assert BuilderChecks.is_equal(loaded_records, _SAMPLES)

    # Delete first and last record
    active(DataSource).delete_many([sample_keys[0], sample_keys[-1]], commit=True)
    loaded_records = [active(DataSource).load_one_or_none(key) for key in sample_keys]
    expected_records = [None, *_SAMPLES[1:-1], None]
    assert BuilderChecks.is_equal(loaded_records, expected_records)

    # Delete all records
    active(DataSource).delete_many(sample_keys, commit=True)
    loaded_records = [active(DataSource).load_one_or_none(key) for key in sample_keys]
    assert loaded_records == [None] * len(_SAMPLES)


def test_record_upsert(multi_db_fixture):
    """Check that an existing entry is overridden when a new entry with the same key is saved."""
    # Create sample and save
    sample = StubDataclass().build()
    active(DataSource).replace_one(sample, commit=True)
    loaded_record = active(DataSource).load_one(sample.get_key())
    assert loaded_record == sample

    # create sample with the same key and save
    override_sample = StubDataclassDerived().build()
    active(DataSource).replace_one(override_sample, commit=True)
    loaded_record = active(DataSource).load_one(sample.get_key())
    assert loaded_record == override_sample

    override_sample = StubDataclassDoubleDerived().build()
    active(DataSource).replace_one(override_sample, commit=True)
    loaded_record = active(DataSource).load_one(sample.get_key())
    assert loaded_record == override_sample


def test_load_by_type(multi_db_fixture):
    """Test 'load_by_type' method."""
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

    active(DataSource).insert_many(all_samples, commit=True)

    loaded_records = active(DataSource).load_by_type(StubDataclass)
    assert PytestUtil.assert_equals_iterable_without_ordering(all_samples, loaded_records)

    loaded_records = active(DataSource).load_by_type(StubDataclassDerived)
    assert PytestUtil.assert_equals_iterable_without_ordering(derived_samples, loaded_records)


def test_singleton(multi_db_fixture):
    """Test singleton type saving."""
    singleton_sample = StubDataclassSingleton().build()
    active(DataSource).replace_one(singleton_sample, commit=True)
    loaded_sample = active(DataSource).load_one(
        singleton_sample.get_key(),
        cast_to=StubDataclassSingleton,
    )
    assert loaded_sample == singleton_sample

    other_singleton_sample = StubDataclassSingleton(str_field="other").build()
    active(DataSource).replace_one(other_singleton_sample, commit=True)
    all_records = list(active(DataSource).load_by_type(other_singleton_sample.__class__))
    assert len(all_records) == 1
    assert all_records[0] == other_singleton_sample


def test_derived_key(multi_db_fixture):
    """Test singleton type saving."""
    sample = StubDataclassPolymorphic().build()
    active(DataSource).insert_one(sample, commit=True)
    loaded_sample = active(DataSource).load_one(
        sample.get_key(),
        cast_to=StubDataclassPolymorphic,
    )
    assert loaded_sample == sample


@pytest.mark.skip(
    "Temporarily skip a test for repeated record save."
)  # TODO(Sasha): Restore if and when tracking repeats is implemented
def test_repeated(multi_db_fixture):
    """Test including the same object twice in save many."""
    record = StubDataclass().build()
    active(DataSource).replace_many([record, record], commit=True)

    loaded_records = list(active(DataSource).load_many([record.get_key()]))
    assert len(loaded_records) == 1
    assert loaded_records[0] == record


def test_load_by_query(multi_db_fixture):
    """Test count_by_query for a string field."""
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc", obj_str_field=None),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    active(DataSource).insert_many(records, commit=True)

    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field="def").build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()

    # Load using a query
    to_key_str_field = lambda rec: [x.key_str_field for x in rec]
    assert to_key_str_field(active(DataSource).load_by_query(eq_query)) == ["def"]
    assert to_key_str_field(active(DataSource).load_by_query(in_query)) == ["def", "xyz"]


def test_load_all_sort_order(multi_db_fixture):
    """Test sort_order for load_all sorts by key field."""
    records = [
        Event(
            timestamp=str(time.time() + i),  # Timestamp is key field, so the sorting will be performed by it
            event_kind=EventKind.LOG,
        ).build()
        for i in range(5)
    ]
    active(DataSource).insert_many(records, commit=True)

    records = active(DataSource).load_all(key_type=Event().get_key_type(), sort_order=SortOrder.DESC)
    assert records == tuple(sorted(records, key=lambda r: r.timestamp, reverse=True))

    records = active(DataSource).load_all(key_type=Event().get_key_type(), sort_order=SortOrder.ASC)
    assert records == tuple(sorted(records, key=lambda r: r.timestamp))


def test_load_query_sort_order(multi_db_fixture):
    """Test sort_order for load_query sorts by key field (for now defaulted to key field)."""
    error_records = [
        StubDataclassDerived(
            derived_str_field="Error",
            id=f"A{i}",
        ).build()
        for i in range(5)
    ]
    info_records = [
        StubDataclassDerived(
            derived_str_field="Info",
            id=f"B{i}",
        ).build()
        for i in range(6)
    ]
    active(DataSource).insert_many(error_records + info_records, commit=True)

    query = StubDataclassDerivedQuery(derived_str_field="Error").build()
    records = active(DataSource).load_by_query(
        query,
        sort_order=SortOrder.DESC,
    )
    assert records == tuple(sorted(error_records, key=lambda r: r.id, reverse=True))

    query = StubDataclassDerivedQuery(derived_str_field="Info").build()
    records = active(DataSource).load_by_query(query, sort_order=SortOrder.ASC)
    assert records == tuple(sorted(info_records, key=lambda r: r.id))


def test_count_by_query(multi_db_fixture):
    """Test count_by_query for a string field."""
    records = [
        StubDataclassPrimitiveFields(key_str_field="abc", obj_str_field=None),
        StubDataclassPrimitiveFields(key_str_field="def"),
        StubDataclassPrimitiveFields(key_str_field="xyz"),
    ]
    records = [x.build() for x in records]
    active(DataSource).insert_many(records, commit=True)

    eq_query = StubDataclassPrimitiveFieldsQuery(key_str_field="def").build()
    in_query = StubDataclassPrimitiveFieldsQuery(key_str_field=In(["def", "xyz"])).build()

    assert active(DataSource).count_by_query(eq_query) == 1
    assert active(DataSource).count_by_query(in_query) == 2


def test_skip_and_limit(multi_db_fixture):
    """Test Dbs work correctly with 'skip' and 'limit' params."""

    records = (
        StubDataclass(id="abc").build(),
        StubDataclass(id="def").build(),
    )

    active(DataSource).insert_many(records=records, commit=True)

    # Load with 'skip'
    load_all_records = active(DataSource).load_all(key_type=StubDataclassKey, skip=2)
    load_by_type_records = active(DataSource).load_by_type(record_type=StubDataclass, skip=2)
    assert len(load_all_records) == 0
    assert len(load_by_type_records) == 0

    # Load with 'limit'
    load_all_records = list(active(DataSource).load_all(key_type=StubDataclassKey, limit=1))
    load_by_type_records = list(active(DataSource).load_by_type(record_type=StubDataclass, limit=1))
    assert len(load_all_records) == 1
    assert len(load_by_type_records) == 1


def test_save_with_parent(multi_db_fixture):
    records = (
        StubDataclass(id="abc").build(),
        StubDataclass(id="def").build(),
    )

    base_data_source = active(DataSource)

    base_data_source.insert_many(records=records, commit=True)

    child_data_source = DataSource(
        db = base_data_source.db,
        dataset=base_data_source.dataset,
        tenant=TenantKey(tenant_id="test_tenant"),
        parent=base_data_source,
    ).build()

    child_data_source.insert_many(records, commit=True)

    base_ds_result = base_data_source.load_by_type(StubDataclass)

    assert not base_ds_result

    child_ds_result = child_data_source.load_by_type(StubDataclass)

    assert PytestUtil.assert_equals_iterable_without_ordering(child_ds_result, records)


if __name__ == "__main__":
    pytest.main([__file__])
