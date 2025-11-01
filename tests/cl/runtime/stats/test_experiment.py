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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.stats.experiment_condition import ExperimentCondition
from stubs.cl.runtime.stats.stub_binary_experiment import StubBinaryExperiment


def test_run_many(multi_db_fixture):
    """Test for the functionality of base Experiment class."""
    # Create and run the experiment with max_trials not set
    max_trials_not_set = StubBinaryExperiment(
        experiment_id="test_run_many.max_trials_not_set",
        conditions=[
            ExperimentCondition(experiment_condition_id="Test1"),
        ],
    )

    # Run the experiment in stages
    assert max_trials_not_set.query_existing_trials() == 0
    assert max_trials_not_set.query_remaining_trials() is None

    max_trials_not_set.run_one()
    assert max_trials_not_set.query_existing_trials() == 1

    max_trials_not_set.run_many(num_trials=3)
    assert max_trials_not_set.query_existing_trials() == 4

    # Create and run the experiment with max_trials set to 5
    max_trials_set = StubBinaryExperiment(
        experiment_id="test_run_many.max_trials_set",
        max_trials=5,
        conditions=[
            ExperimentCondition(experiment_condition_id="Test1"),
        ],
    )

    # Run the experiment in stages
    assert max_trials_set.query_existing_trials() == 0
    assert max_trials_set.query_remaining_trials() == 5

    max_trials_set.run_one()
    assert max_trials_set.query_existing_trials() == 1
    assert max_trials_set.query_remaining_trials() == 4

    max_trials_set.run_many(num_trials=3)
    assert max_trials_set.query_existing_trials() == 4
    assert max_trials_set.query_remaining_trials() == 1

    # Stop when max_trials is reached
    max_trials_set.run_many(num_trials=3)
    assert max_trials_set.query_existing_trials() == 5
    assert max_trials_set.query_remaining_trials() == 0

    # No trials remaining, error message
    with pytest.raises(RuntimeError, match="has already been reached"):
        max_trials_set.run_many(num_trials=3)
    assert max_trials_set.query_existing_trials() == 5
    assert max_trials_set.query_remaining_trials() == 0


def test_run_all(multi_db_fixture):
    """Test for the functionality of base Experiment class."""
    # Create and run the experiment with max_trials not set
    max_trials_not_set = StubBinaryExperiment(
        experiment_id="test_run_all.max_trials_not_set",
        conditions=[
            ExperimentCondition(experiment_condition_id="Test1"),
        ],
    )

    with pytest.raises(RuntimeError):
        # Cannot run_all if max_trials is not set
        max_trials_not_set.run_all()

    # Create and run the experiment with max_trials set to 5
    max_trials_set = StubBinaryExperiment(
        experiment_id="test_run_all.max_trials_set",
        max_trials=5,
        conditions=[
            ExperimentCondition(experiment_condition_id="Test1"),
        ],
    )

    # Run the experiment in stages
    assert max_trials_set.query_existing_trials() == 0
    assert max_trials_set.query_remaining_trials() == 5

    max_trials_set.run_one()
    assert max_trials_set.query_existing_trials() == 1
    assert max_trials_set.query_remaining_trials() == 4

    max_trials_set.run_all()
    assert max_trials_set.query_existing_trials() == 5
    assert max_trials_set.query_remaining_trials() == 0

    # No trials remaining, error message
    with pytest.raises(RuntimeError, match="has already been reached"):
        max_trials_set.run_all()
    assert max_trials_set.query_existing_trials() == 5
    assert max_trials_set.query_remaining_trials() == 0


if __name__ == "__main__":
    pytest.main([__file__])
