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
from cl.runtime.experiments.experiment_key_query import ExperimentKeyQuery
from cl.runtime.qa.pytest.pytest_fixtures import pytest_default_db  # noqa
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.table_binding import TableBinding
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

def test_bindings(pytest_default_db):  # TODO: Extend to multiple DBs
    """Test the methods related to bindings."""

    stubs = _multiple_table_stubs()
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

def test_load_where(pytest_default_db):  # TODO: Extend to multiple DBs
    """Test load_type for dynamic table names."""

    stubs = _multiple_table_stubs()
    DbContext.save_many(stubs)

    # Load table 'ExperimentTable1'
    query = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable1")).build()
    result_1 = DbContext.load_where(query)
    assert result_1 == (stubs[0], stubs[1])

    # Load table 'ExperimentTable2'
    query = ExperimentKeyQuery(experiment_type=ExperimentTypeKey(experiment_type_id="ExperimentTable2")).build()
    result_2 = DbContext.load_where(query)
    assert result_2 == (stubs[2], stubs[3])


if __name__ == "__main__":
    pytest.main([__file__])
