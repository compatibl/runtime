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

from dataclasses import dataclass
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.experiments.supervised_binary_experiment import SupervisedBinaryExperiment
from cl.runtime.experiments.supervised_binary_trial import SupervisedBinaryTrial


@dataclass(slots=True, kw_only=True)
class StubSupervisedBinaryExperiment(SupervisedBinaryExperiment):
    """Stub implementation of SupervisedBinaryExperiment."""

    def run_one(self) -> None:

        # Exit if there are no remaining trials
        if self.is_max_trials_reached_or_exceeded():
            return

        # Create a trial record with random result
        trial = SupervisedBinaryTrial(
            experiment=self.get_key(),
            actual_outcome=True,
            expected_outcome=True,
        ).build()
        DbContext.save_one(trial)
