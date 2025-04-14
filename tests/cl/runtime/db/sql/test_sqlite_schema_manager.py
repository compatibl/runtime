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
from cl.runtime.db.sql.sqlite_schema_manager import SqliteSchemaManager
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.record_util import RecordUtil
from cl.runtime.schema.type_info_cache import TypeInfoCache
from stubs.cl.runtime import StubDataclassDerivedFromDerivedRecord
from stubs.cl.runtime import StubDataclassDerivedRecord
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOtherDerivedRecord
from stubs.cl.runtime import StubDataclassRecord
from stubs.cl.runtime import StubDataclassRecordKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields


# TODO (Roman): move to Schema tests
def test_get_subtypes_in_hierarchy():
    result = TypeInfoCache.get_child_names(StubDataclassRecordKey)
    expected_classes = {
        StubDataclassRecordKey,
        StubDataclassRecord,
        StubDataclassDerivedRecord,
        StubDataclassDerivedFromDerivedRecord,
        StubDataclassDictFields,
        StubDataclassDictListFields,
        StubDataclassListDictFields,
        StubDataclassListFields,
        StubDataclassTupleFields,
        StubDataclassOtherDerivedRecord,
        StubDataclassNestedFields,
    }
    expected_names = {x.__name__ for x in expected_classes}

    assert len(result) == len(expected_names)
    assert set(result) == expected_names


# TODO (Roman): move to Schema tests
def test_get_key_class():
    samples = (
        StubDataclassRecord,
        StubDataclassDerivedRecord,
        StubDataclassDerivedFromDerivedRecord,
        StubDataclassDictFields,
        StubDataclassDictListFields,
        StubDataclassListDictFields,
        StubDataclassListFields,
        StubDataclassOtherDerivedRecord,
    )
    for type_ in samples:
        assert type_.get_key_type() == StubDataclassRecordKey


def test_get_columns_mapping():
    test_type = StubDataclassDerivedFromDerivedRecord
    expected_columns = {
        "_type": "_type",
        "id": "StubDataclassRecordKey.id",
        "derived_str_field": "StubDataclassDerivedRecord.derived_str_field",
        "str_dict": "StubDataclassDictFields.str_dict",
        "float_dict": "StubDataclassDictFields.float_dict",
        "date_dict": "StubDataclassDictFields.date_dict",
        "data_dict": "StubDataclassDictFields.data_dict",
        "key_dict": "StubDataclassDictFields.key_dict",
        "record_dict": "StubDataclassDictFields.record_dict",
        "derived_record_dict": "StubDataclassDictFields.derived_record_dict",
        "float_dict_list": "StubDataclassDictListFields.float_dict_list",
        "date_dict_list": "StubDataclassDictListFields.date_dict_list",
        "record_dict_list": "StubDataclassDictListFields.record_dict_list",
        "derived_record_dict_list": "StubDataclassDictListFields.derived_record_dict_list",
        "float_list_dict": "StubDataclassListDictFields.float_list_dict",
        "date_list_dict": "StubDataclassListDictFields.date_list_dict",
        "record_list_dict": "StubDataclassListDictFields.record_list_dict",
        "derived_record_list_dict": "StubDataclassListDictFields.derived_record_list_dict",
        "str_list": "StubDataclassListFields.str_list",
        "float_list": "StubDataclassListFields.float_list",
        "date_list": "StubDataclassListFields.date_list",
        "data_list": "StubDataclassListFields.data_list",
        "key_list": "StubDataclassListFields.key_list",
        "record_list": "StubDataclassListFields.record_list",
        "derived_record_list": "StubDataclassListFields.derived_record_list",
        "other_derived": "StubDataclassOtherDerivedRecord.other_derived",
    }

    guard = RegressionGuard()
    resolved_columns = SqliteSchemaManager().get_columns_mapping(test_type)
    tuple(guard.write(f"{key},{value}") for key, value in resolved_columns.items())
    guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
