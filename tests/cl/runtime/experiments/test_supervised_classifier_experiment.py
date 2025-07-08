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
from cl.runtime.experiments.experiment_scenario import ExperimentScenario
from cl.runtime.experiments.experiment_type import ExperimentType
from cl.runtime.experiments.experiment_type_key import ExperimentTypeKey
from cl.runtime.qa.pytest.pytest_fixtures import patch_uuid_conversion  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_basic_mongo_mock_db  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa
from stubs.cl.runtime.experiments.stub_supervised_classifier_experiment import StubSupervisedClassifierExperiment


def test_smoke(pytest_basic_mongo_mock_db):
    """Test for BinaryExperiment class with supervised=True."""

    exp_type = ExperimentType(experiment_type_id="Test").build()
    sc1 = ExperimentScenario(
        experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
        experiment_scenario_id="Test1"
    ).build()

    DbContext.current().save_one(exp_type)
    DbContext.current().save_one(sc1)

    # Create and run the experiment
    experiment = StubSupervisedClassifierExperiment(
        experiment_type=ExperimentTypeKey(experiment_type_id="TestSupervisedClassifierExperiment"),
        experiment_id="test_supervised_classifier_experiment.test_smoke",
        class_labels=["A", "B", "C"],
        max_trials=5,
        scenarios=[
            ExperimentScenario(
                experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
                experiment_scenario_id="Test1"
            ),
        ]
    )
    experiment.run_all()


def test_experiment_plot(pytest_basic_mongo_mock_db, pytest_work_dir):

    exp_type = ExperimentType(experiment_type_id="Test").build()
    sc1 = ExperimentScenario(
        experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
        experiment_scenario_id="Test1"
    ).build()
    sc2 = ExperimentScenario(
        experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
        experiment_scenario_id="Test2"
    ).build()

    DbContext.current().save_one(exp_type)
    DbContext.current().save_many([sc1, sc2])

    experiment = StubSupervisedClassifierExperiment(
        experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
        experiment_id="Test",
        scenarios=[
            ExperimentScenario(
                experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
                experiment_scenario_id="Test1"
            ),
            ExperimentScenario(
                experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
                experiment_scenario_id="Test2"
            ),
            ExperimentScenario(
                experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
                experiment_scenario_id="Test3"
            ),
            ExperimentScenario(
                experiment_type=ExperimentTypeKey(experiment_type_id="Test"),
                experiment_scenario_id="Test4"
            ),
        ],
        max_trials=5,
        class_labels=["A", "B", "C"]
    )
    experiment.run_all()

    experiment.get_plot("test_supervised_classifier_experiment.supervised_classifier_experiment_plot").save(format_="svg")


if __name__ == "__main__":
    pytest.main([__file__])
