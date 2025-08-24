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
from cl.runtime.stats.experiment_kind import ExperimentKind
from cl.runtime.stats.experiment_kind_key import ExperimentKindKey
from cl.runtime.stats.experiment_scenario import ExperimentScenario
from stubs.cl.runtime.stats.stub_classifier_experiment import StubClassifierExperiment


def test_smoke(multi_db_fixture):
    """Test for ClassifierExperimentMixin."""

    exp_type = ExperimentKind(kind_id="Test").build()
    sc1 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1").build()

    active(DataSource).replace_one(exp_type, commit=True)
    active(DataSource).replace_one(sc1, commit=True)

    # Create and run the experiment
    experiment = StubClassifierExperiment(
        experiment_kind=ExperimentKindKey(kind_id="TestClassifierExperiment"),
        experiment_id="test_classifier_experiment.test_smoke",
        max_trials=5,
        class_labels=["A", "B", "C"],
        scenarios=[
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1"),
        ],
    )
    experiment.run_all()


def test_plot(multi_db_fixture, work_dir_fixture):
    exp_type = ExperimentKind(kind_id="Test").build()
    sc1 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1").build()
    sc2 = ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test2").build()

    active(DataSource).replace_one(exp_type, commit=True)
    active(DataSource).replace_many([sc1, sc2], commit=True)

    experiment = StubClassifierExperiment(
        experiment_kind=ExperimentKindKey(kind_id="Test"),
        experiment_id="Test",
        scenarios=[
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test1"),
            ExperimentScenario(experiment_kind=ExperimentKindKey(kind_id="Test"), experiment_scenario_id="Test2"),
        ],
        max_trials=5,
        class_labels=["A", "B", "C"],
    )
    random.seed(0)
    experiment.run_all()

    experiment.get_plot("test_classifier_experiment.classifier_experiment_plot").save(format_="svg")


if __name__ == "__main__":
    pytest.main([__file__])
