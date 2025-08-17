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
import random
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.experiments.experiment_kind import ExperimentKind
from cl.runtime.experiments.experiment_kind_key import ExperimentKindKey
from cl.runtime.experiments.experiment_scenario import ExperimentScenario
from stubs.cl.runtime.experiments.stub_supervised_binary_experiment import StubSupervisedBinaryExperiment


def test_smoke(multi_db_fixture):
    """Test for SupervisedBinaryExperiment class."""

    exp_type = ExperimentKind(kind_id="Test").build()
    sc1 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1").build()

    active(DataSource).replace_one(exp_type)
    active(DataSource).replace_one(sc1)

    # Create and run the experiment
    experiment = StubSupervisedBinaryExperiment(
        experiment_kind=ExperimentKindKey(kind_id="TestSupervisedBinaryExperiment"),
        experiment_id="test_supervised_binary_experiment.test_smoke",
        max_trials=5,
        scenarios=[
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1"),
        ],
    )
    experiment.run_all()


def test_plot(multi_db_fixture, work_dir_fixture):

    exp_type = ExperimentKind(kind_id="Test").build()
    sc1 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1").build()
    sc2 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test2").build()

    active(DataSource).replace_one(exp_type)
    active(DataSource).replace_many([sc1, sc2])

    experiment = StubSupervisedBinaryExperiment(
        experiment_kind=ExperimentKindKey(kind_id="Test"),
        experiment_id="Test",
        scenarios=[
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1"),
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test2"),
        ],
        max_trials=5,
    )
    random.seed(0)
    experiment.run_all()

    experiment.get_plot("test_supervised_binary_experiment.supervised_binary_experiment_plot").save(format_="svg")


if __name__ == "__main__":
    pytest.main([__file__])
