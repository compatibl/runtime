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
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.experiment_key_query import ExperimentKeyQuery
from cl.runtime.experiments.experiment_type_key import ExperimentTypeKey
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.records.table_binding import TableBinding
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment


def _multiple_table_records():
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


def test_bindings(pytest_default_db):  # TODO: Extend to multiple DBs
    """Test the methods related to bindings."""

    stubs = _multiple_table_records()
    DbContext.save_many(stubs)

    bindings = DbContext.get_bindings()
    assert bindings == (
        TableBinding(table="ExperimentTable1", key_type="ExperimentKey"),
        TableBinding(table="ExperimentTable2", key_type="ExperimentKey"),
        TableBinding(table="TableBindingKey", key_type="TableBindingKey"),
    )

    bound_tables = DbContext.get_bound_tables(key_type=ExperimentKey)
    assert bound_tables == ("ExperimentTable1", "ExperimentTable2")

    bound_type = DbContext.get_bound_type(table="ExperimentTable1")
    assert bound_type == ExperimentKey


def test_load_table(pytest_default_db):  # TODO: Extend to multiple DBs
    """Test load_table for dynamic table names."""

    records = _multiple_table_records()
    DbContext.save_many(records)

    # Load table 'ExperimentTable1'
    result_1 = DbContext.load_table("ExperimentTable1")
    assert result_1 == (records[0], records[1])

    # Load table 'ExperimentTable2'
    result_2 = DbContext.load_table("ExperimentTable2")
    assert result_2 == (records[2], records[3])

    # Test limit and skip for 'ExperimentTable1'
    for limit in range(0, len(result_1)):
        for skip in range(0, len(result_1)):
            actual_result = DbContext.load_table("ExperimentTable1", limit=limit, skip=skip)
            expected_result = tuple(result_1[skip : skip + limit])
            assert actual_result == expected_result

    # Test limit and skip for 'ExperimentTable2'
    for limit in range(0, len(result_2)):
        for skip in range(0, len(result_2)):
            actual_result = DbContext.load_table("ExperimentTable2", limit=limit, skip=skip)
            expected_result = tuple(result_2[skip : skip + limit])
            assert actual_result == expected_result


def test_load_where(pytest_default_db):  # TODO: Extend to multiple DBs
    """Test load_type for dynamic table names."""

    records = _multiple_table_records()
    DbContext.save_many(records)

    # Load table 'ExperimentTable1'
    query_1 = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1")).build()
    result_1 = DbContext.load_where(query_1)
    assert result_1 == (records[0], records[1])

    # Load table 'ExperimentTable2'
    query_2 = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2")).build()
    result_2 = DbContext.load_where(query_2)
    assert result_2 == (records[2], records[3])

    # Test limit and skip for 'ExperimentTable1'
    for limit in range(0, len(result_1)):
        for skip in range(0, len(result_1)):
            actual_result = DbContext.load_where(query_1, limit=limit, skip=skip)
            expected_result = tuple(result_1[skip : skip + limit])
            assert actual_result == expected_result

    # Test limit and skip for 'ExperimentTable2'
    for limit in range(0, len(result_2)):
        for skip in range(0, len(result_2)):
            actual_result = DbContext.load_where(query_2, limit=limit, skip=skip)
            expected_result = tuple(result_2[skip : skip + limit])
            assert actual_result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
