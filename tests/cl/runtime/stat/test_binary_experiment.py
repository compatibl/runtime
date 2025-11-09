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
from stubs.cl.runtime.stat.stub_binary_experiment import StubBinaryExperiment


def test_smoke(multi_db_fixture):
    """Test for BinaryExperiment class."""
    # Create and run the experiment
    experiment = StubBinaryExperiment(
        experiment_id="test_binary_experiment.test_smoke",
        max_trials=5,
    ).build()
    experiment.run_launch_all_trials()
    trials = experiment.view_trials()
    assert len(trials) == 5


def test_plot(multi_db_fixture, work_dir_fixture):
    experiment = StubBinaryExperiment(
        experiment_id="Test",
        conditions=[
            Param(param_id="Test1"),
            Param(param_id="Test2"),
        ],
        max_trials=5,
    )
    random.seed(0)
    experiment.run_launch_all_trials()

    experiment.get_plot("test_binary_experiment_plot.binary_experiment_plot").save(format_="svg")


if __name__ == "__main__":
    pytest.main([__file__])
