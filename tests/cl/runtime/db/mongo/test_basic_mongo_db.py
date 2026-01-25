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
from cl.runtime.db.mongo.basic_mongo_db import BasicMongoDb
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.records.typename import typename
from cl.runtime.stat.experiment_key_query import ExperimentKeyQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_nested_fields_query import StubDataclassNestedFieldsQuery
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields import StubDataclassPrimitiveFields
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_primitive_fields_query import (
    StubDataclassPrimitiveFieldsQuery,
)


def test_check_db_id():
    """Test that _get_db_name method correctly detects invalid names."""
    # Check for length
    BasicMongoDb(db_id="a" * 63)._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="a" * 64)._get_db_name()

    # Letters, numbers and underscore are allowed
    BasicMongoDb(db_id="abc")._get_db_name()
    BasicMongoDb(db_id="123")._get_db_name()
    BasicMongoDb(db_id="abc_xyz")._get_db_name()

    # Semicolon is allowed even though it is not in the suggested list
    BasicMongoDb(db_id="abc;xyz")._get_db_name()

    # Check for space
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc xyz")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc ")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id=" xyz")._get_db_name()

    # Check for period
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc.xyz")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc.")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id=".xyz")._get_db_name()

    # Check for other symbols
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc:xyz")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc|xyz")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc\\xyz")._get_db_name()
    with pytest.raises(RuntimeError):
        BasicMongoDb(db_id="abc/xyz")._get_db_name()


def test_populate_index_dict():
    """Test BasicMongoDB._populate_index_dict method."""
    sample_types = (
        StubDataclassPrimitiveFields,
        StubDataclassPrimitiveFieldsQuery,
        StubDataclassNestedFieldsQuery,
        ExperimentKeyQuery,
    )
    for sample_type in sample_types:
        index_list = []
        BasicMongoDb(db_id=typename(sample_type)).build()._populate_index(
            type_=sample_type,
            result=index_list,
        )
        index_dict = dict(index_list)
        RegressionGuard(prefix=typename(sample_type)).build().write(index_dict)
    RegressionGuard().build().verify_all()


if __name__ == "__main__":
    pytest.main([__file__])
