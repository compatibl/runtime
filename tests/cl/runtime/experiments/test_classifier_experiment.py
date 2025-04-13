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
from stubs.cl.runtime.experiments.stub_binary_experiment import StubBinaryExperiment
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa
from stubs.cl.runtime.experiments.stub_classifier_experiment import StubClassifierExperiment


def test_supervised(pytest_work_dir):
    """Test for BinaryExperiment class with supervised=True."""

    # Create and run the experiment
    experiment = StubClassifierExperiment(
        experiment_id="classifier_experiment",
        supervised=True,
        max_trials=5,
    )
    experiment.run_all()


if __name__ == "__main__":
    pytest.main([__file__])
