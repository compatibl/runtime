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
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.stat.case import Case
from stubs.cl.runtime.stat.stub_classifier_experiment import StubClassifierExperiment


def test_smoke(multi_db_fixture):
    """Test for ClassifierExperiment."""
    # Create and run the experiment
    experiment = StubClassifierExperiment(
        experiment_id=f"test_classifier_experiment.test_smoke.{Timestamp.create()}",
        num_trials=5,
        class_labels=["A", "B", "C"],
        cases=[
            Case(param_id="Test1"),
        ],
    )
    experiment.run_run()


def test_plot(multi_db_fixture, work_dir_fixture):
    experiment = StubClassifierExperiment(
        experiment_id=f"Test.{Timestamp.create()}",
        cases=[
            Case(param_id="Test1"),
            Case(param_id="Test2"),
        ],
        num_trials=5,
        class_labels=["A", "B", "C"],
    )
    random.seed(0)
    experiment.run_run()

    experiment.get_plot("test_classifier_experiment.classifier_experiment_plot").save(format_="svg")


if __name__ == "__main__":
    pytest.main([__file__])
