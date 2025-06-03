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
from cl.runtime.schema.type_info_cache import TypeInfoCache
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassKey
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_tuple_fields import StubDataclassTupleFields


# TODO (Roman): move to Schema tests
def test_get_subtypes_in_hierarchy():
    result = TypeInfoCache.get_child_names(StubDataclassKey)
    expected_classes = {
        StubDataclassKey,
        StubDataclass,
        StubDataclassDerived,
        StubDataclassDoubleDerived,
        StubDataclassDictFields,
        StubDataclassDictListFields,
        StubDataclassListDictFields,
        StubDataclassListFields,
        StubDataclassTupleFields,
        StubDataclassOtherDerived,
        StubDataclassNestedFields,
    }
    expected_names = {x.__name__ for x in expected_classes}

    assert len(result) == len(expected_names)
    assert set(result) == expected_names


# TODO (Roman): move to Schema tests
def test_get_key_class():
    samples = (
        StubDataclass,
        StubDataclassDerived,
        StubDataclassDoubleDerived,
        StubDataclassDictFields,
        StubDataclassDictListFields,
        StubDataclassListDictFields,
        StubDataclassListFields,
        StubDataclassOtherDerived,
    )
    for type_ in samples:
        assert type_.get_key_type() == StubDataclassKey


def test_get_columns_mapping():
    test_type = StubDataclassDoubleDerived
    expected_columns = {
        "_type": "_type",
        "id": "StubDataclassKey.id",
        "derived_str_field": "StubDataclassDerived.derived_str_field",
        "str_dict": "StubDataclassDictFields.str_dict",
        "float_dict": "StubDataclassDictFields.float_dict",
        "date_dict": "StubDataclassDictFields.date_dict",
        "data_dict": "StubDataclassDictFields.data_dict",
        "key_dict": "StubDataclassDictFields.key_dict",
        "record_dict": "StubDataclassDictFields.record_dict",
        "derived_dict": "StubDataclassDictFields.derived_dict",
        "float_dict_list": "StubDataclassDictListFields.float_dict_list",
        "date_dict_list": "StubDataclassDictListFields.date_dict_list",
        "record_dict_list": "StubDataclassDictListFields.record_dict_list",
        "derived_dict_list": "StubDataclassDictListFields.derived_dict_list",
        "float_list_dict": "StubDataclassListDictFields.float_list_dict",
        "date_list_dict": "StubDataclassListDictFields.date_list_dict",
        "record_list_dict": "StubDataclassListDictFields.record_list_dict",
        "derived_list_dict": "StubDataclassListDictFields.derived_list_dict",
        "str_list": "StubDataclassListFields.str_list",
        "float_list": "StubDataclassListFields.float_list",
        "date_list": "StubDataclassListFields.date_list",
        "data_list": "StubDataclassListFields.data_list",
        "key_list": "StubDataclassListFields.key_list",
        "record_list": "StubDataclassListFields.record_list",
        "derived_list": "StubDataclassListFields.derived_list",
        "other_derived": "StubDataclassOtherDerived.other_derived",
    }

    guard = RegressionGuard()
    resolved_columns = SqliteSchemaManager().get_columns_mapping(test_type)
    tuple(guard.write(f"{key},{value}") for key, value in resolved_columns.items())
    guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
