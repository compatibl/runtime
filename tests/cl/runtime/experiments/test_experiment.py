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
from cl.runtime.qa.pytest.pytest_fixtures import patch_uuid_conversion  # noqa
from cl.runtime.qa.pytest.pytest_fixtures import pytest_basic_mongo_mock_db  # noqa


def test_run(pytest_basic_mongo_mock_db):
    """Test for the functionality of base Experiment class."""

    # Create and run the experiment
    experiment = StubBinaryExperiment(
        experiment_id="2",
        supervised=True,
        max_trials=10,
    )

    # Run the experiment in stages
    assert experiment.count_existing_trials() == 0
    assert experiment.count_remaining_trials() == 10
    experiment.run_one()
    assert experiment.count_remaining_trials() == 9
    experiment.run_many(num_trials=3)
    assert experiment.count_remaining_trials() == 6
    experiment.run_one()
    assert experiment.count_remaining_trials() == 5
    experiment.run_all()
    assert experiment.count_existing_trials() == 10
    assert experiment.count_remaining_trials() == 0

    # Error for run_one when no trials are remaining
    with pytest.raises(RuntimeError):
        experiment.run_one()

    experiment.run_many(num_trials=3)
    assert experiment.count_existing_trials() == 10
    assert experiment.count_remaining_trials() == 0

    experiment.run_all()
    assert experiment.count_existing_trials() == 10
    assert experiment.count_remaining_trials() == 0


if __name__ == "__main__":
    pytest.main([__file__])
