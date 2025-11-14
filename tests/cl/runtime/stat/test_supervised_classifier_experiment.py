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
from cl.runtime.params.param import Param
from cl.runtime.primitive.timestamp import Timestamp
from stubs.cl.runtime.stat.stub_supervised_classifier_experiment import StubSupervisedClassifierExperiment


def test_smoke(multi_db_fixture):
    """Test for BinaryExperiment class with supervised=True."""
    # Create and run the experiment
    experiment = StubSupervisedClassifierExperiment(
        experiment_id=f"test_supervised_classifier_experiment.test_smoke.{Timestamp.create()}",
        class_labels=["A", "B", "C"],
        max_trials=5,
        cases=[
            Param(param_id="Test1"),
        ],
    )
    experiment._resume()


def test_plot(multi_db_fixture, work_dir_fixture):
    experiment = StubSupervisedClassifierExperiment(
        experiment_id=f"Test.{Timestamp.create()}",
        cases=[
            Param(param_id="Test1"),
            Param(param_id="Test2"),
            Param(param_id="Test3"),
            Param(param_id="Test4"),
        ],
        max_trials=15,
        class_labels=["A", "B", "C"],
    )
    random.seed(0)
    experiment._resume()

    experiment.get_plot("test_supervised_classifier_experiment.supervised_classifier_experiment_plot").save(
        format_="svg"
    )


if __name__ == "__main__":
    pytest.main([__file__])
