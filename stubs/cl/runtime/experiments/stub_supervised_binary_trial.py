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
from cl.runtime.experiments.supervised_binary_trial_mixin import SupervisedBinaryTrialMixin
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.experiments.stub_supervised_binary_experiment_key import StubSupervisedBinaryExperimentKey
from stubs.cl.runtime.experiments.stub_supervised_binary_trial_key import StubSupervisedBinaryTrialKey


@dataclass(slots=True, kw_only=True)
class StubSupervisedBinaryTrial(
    StubSupervisedBinaryTrialKey,
    SupervisedBinaryTrialMixin[StubSupervisedBinaryTrialKey, StubSupervisedBinaryExperimentKey],
):
    """Single trial of an unsupervised experiment where each trial has True or False outcome."""

    experiment: StubSupervisedBinaryExperimentKey = required()
    """Experiment for which the trial is recorded."""

    result: bool = required()
    """Result of the trial (True or False)."""

    expected: bool = required()
    """Expected result of the trial (True or False)."""

    def get_key(self) -> StubSupervisedBinaryTrialKey:
        return StubSupervisedBinaryTrialKey(timestamp=self.timestamp).build()
