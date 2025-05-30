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
from cl.runtime.experiments.supervised_classifier_trial_mixin import SupervisedClassifierTrialMixin
from cl.runtime.records.for_dataclasses.extensions import required
from stubs.cl.runtime.experiments.stub_supervised_classifier_experiment_key import StubSupervisedClassifierExperimentKey
from stubs.cl.runtime.experiments.stub_supervised_classifier_trial_key import StubSupervisedClassifierTrialKey


@dataclass(slots=True, kw_only=True)
class StubSupervisedClassifierTrial(
    StubSupervisedClassifierTrialKey,
    SupervisedClassifierTrialMixin[StubSupervisedClassifierTrialKey, StubSupervisedClassifierExperimentKey],
):
    """Single trial of an unsupervised experiment where each trial has True or False outcome."""

    experiment: StubSupervisedClassifierExperimentKey = required()
    """Experiment for which the trial is recorded."""

    result: str = required()
    """Result of the trial (class label)."""

    expected: str = required()
    """Expected result of the trial (class label)."""

    def get_key(self) -> StubSupervisedClassifierTrialKey:
        return StubSupervisedClassifierTrialKey(timestamp=self.timestamp).build()
