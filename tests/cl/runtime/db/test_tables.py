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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.experiments.experiment import Experiment
from cl.runtime.experiments.experiment_key_query import ExperimentKeyQuery
from cl.runtime.experiments.experiment_type_key import ExperimentTypeKey
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment
from stubs.cl.runtime.experiments.stub_classifier_experiment import StubClassifierExperiment


def _multiple_table_records():
    """Return stubs with multiple tables."""

    stub_experiments_table_1 = [
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1"),
            experiment_id="StubExperiment11",
        ).build(),
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1"),
            experiment_id="StubExperiment12",
        ).build(),
        StubClassifierExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1"),
            experiment_id="StubExperiment13",
        ).build(),
    ]

    stub_experiments_table_2 = [
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2"),
            experiment_id="StubExperiment21",
        ).build(),
        StubClassifierExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2"),
            experiment_id="StubExperiment22",
        ).build(),
        StubBinaryExperiment(
            experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2"),
            experiment_id="StubExperiment23",
        ).build(),
    ]

    return [*stub_experiments_table_1, *stub_experiments_table_2]


def test_bindings(multi_db_fixture):
    """Test the methods related to bindings."""

    stubs = _multiple_table_records()
    active(DataSource).save_many(stubs)

    bindings = active(DataSource).get_bindings()
    RegressionGuard(channel="bindings").write(bindings)

    tables = active(DataSource).get_tables()
    RegressionGuard(channel="tables").write(tables)

    bound_tables = active(DataSource).get_bound_tables(record_type=Experiment)
    RegressionGuard(channel="bound_tables").write(bound_tables)

    bound_record_type_names = active(DataSource).get_bound_record_type_names(table="ExperimentTable1")
    RegressionGuard(channel="bound_record_type_names").write(bound_record_type_names)

    lowest_bound_record_type_name = active(DataSource).get_lowest_bound_record_type_name(table="ExperimentTable1")
    RegressionGuard(channel="lowest_bound_record_type_name").write(lowest_bound_record_type_name)

    RegressionGuard().verify_all()


def test_load_table(multi_db_fixture):
    """Test load_table for dynamic table names."""

    records = _multiple_table_records()
    active(DataSource).save_many(records)

    # Load table 'ExperimentTable1'
    result_1 = active(DataSource).load_table("ExperimentTable1")
    assert result_1 == (records[0], records[1], records[2])

    # Load table 'ExperimentTable2'
    result_2 = active(DataSource).load_table("ExperimentTable2")
    assert result_2 == (records[3], records[4], records[5])

    # Test limit and skip for 'ExperimentTable1'
    for limit in range(0, len(result_1)):
        for skip in range(0, len(result_1)):
            actual_result = active(DataSource).load_table("ExperimentTable1", limit=limit, skip=skip)
            expected_result = tuple(result_1[skip : skip + limit])
            assert actual_result == expected_result

    # Test limit and skip for 'ExperimentTable2'
    for limit in range(0, len(result_2)):
        for skip in range(0, len(result_2)):
            actual_result = active(DataSource).load_table("ExperimentTable2", limit=limit, skip=skip)
            expected_result = tuple(result_2[skip : skip + limit])
            assert actual_result == expected_result


def test_load_where(multi_db_fixture):
    """Test load_type for dynamic table names."""

    records = _multiple_table_records()
    active(DataSource).save_many(records)

    # Load table 'ExperimentTable1'
    query_1 = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1")).build()
    result_1 = active(DataSource).load_where(query_1)
    assert result_1 == (records[0], records[1], records[2])

    # Load table 'ExperimentTable2'
    query_2 = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2")).build()
    result_2 = active(DataSource).load_where(query_2)
    assert result_2 == (records[3], records[4], records[5])

    # Test limit and skip for 'ExperimentTable1'
    for limit in range(0, len(result_1)):
        for skip in range(0, len(result_1)):
            actual_result = active(DataSource).load_where(query_1, limit=limit, skip=skip)
            expected_result = tuple(result_1[skip : skip + limit])
            assert actual_result == expected_result

    # Test limit and skip for 'ExperimentTable2'
    for limit in range(0, len(result_2)):
        for skip in range(0, len(result_2)):
            actual_result = active(DataSource).load_where(query_2, limit=limit, skip=skip)
            expected_result = tuple(result_2[skip : skip + limit])
            assert actual_result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
