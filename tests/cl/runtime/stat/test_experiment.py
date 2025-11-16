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
from cl.runtime.stat.case import Case
from cl.runtime.primitive.timestamp import Timestamp
from stubs.cl.runtime.stat.stub_binary_experiment import StubBinaryExperiment


def test_resume(multi_db_fixture):
    """Test for the functionality of base Experiment class."""

    # Create and run the experiment with num_trials set to 5
    num_trials_set = StubBinaryExperiment(
        experiment_id=f"test_launch_all_trials.num_trials_set.{Timestamp.create()}",
        num_trials=2,
        cases=[
            Case(param_id="Test1"),
        ],
    ).build()

    # Run the experiment in stages
    assert num_trials_set.calc_num_completed_trials() == (0,)
    assert num_trials_set.calc_num_additional_trials() == (2,)

    num_trials_set.run_run()
    assert num_trials_set.calc_num_completed_trials() == (2,)
    assert num_trials_set.calc_num_additional_trials() == (0,)


if __name__ == "__main__":
    pytest.main([__file__])
