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
from cl.runtime import TypeInfoCache
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.experiments.binary_experiment import BinaryExperiment
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.experiment_type_key import ExperimentTypeKey
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.table_util import TableUtil
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment


def _multiple_table_stubs():
    """Return stubs with multiple tables."""

    stub_experiments_table_1 = [
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1"),
            experiment_id="StubExperiment1",
        ).build(),
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1"),
            experiment_id="StubExperiment2",
        ).build(),
    ]

    stub_experiments_table_2 = [
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2"),
            experiment_id="StubExperiment3",
        ).build(),
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2"),
            experiment_id="StubExperiment4",
        ).build(),
    ]

    return [*stub_experiments_table_1, *stub_experiments_table_2]


def test_save_table(pytest_default_db):
    """Test saving records of the same type to different tables."""

    stubs = _multiple_table_stubs()
    DbContext.save_many(stubs)

    created_table_names = [x.table_id for x in TableUtil.get_tables()]

    # Check expected tables
    assert PytestUtil.assert_equals_iterable_without_ordering(
        created_table_names, ["ExperimentTable1", "ExperimentTable2", "TableKey"]
    )


def test_table_schema_type(pytest_default_db):
    """Test get type from table name."""

    stubs = _multiple_table_stubs()
    DbContext.save_many(stubs)

    # Add table prefix and get class for synthetic type name
    table_synthetic_type_name = TableUtil.add_table_prefix("ExperimentTable1")
    table_type = TypeInfoCache.get_class_from_type_name(table_synthetic_type_name)

    # Check table type. Temporary it is a first child from key class
    assert table_type == BinaryExperiment


def test_load_table(pytest_default_db):
    """Test load records of the same type from different tables."""

    stubs = _multiple_table_stubs()
    DbContext.save_many(stubs)

    # Load all tables for key type
    actual_result = DbContext.load_all(ExperimentKey)
    assert PytestUtil.assert_equals_iterable_without_ordering(actual_result, stubs)

    # Load table 'ExperimentTable1'
    actual_result = DbContext.load_all(ExperimentKey, tables=["ExperimentTable1"])
    assert PytestUtil.assert_equals_iterable_without_ordering(actual_result, [stubs[0], stubs[1]])

    # Load table 'ExperimentTable2'
    actual_result = DbContext.load_all(ExperimentKey, tables=["ExperimentTable2"])
    assert PytestUtil.assert_equals_iterable_without_ordering(actual_result, [stubs[2], stubs[3]])


if __name__ == "__main__":
    pytest.main([__file__])
