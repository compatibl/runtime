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
from cl.runtime.experiments.supervised_binary_experiment_mixin import SupervisedBinaryExperimentMixin
from stubs.cl.runtime.experiments.stub_supervised_binary_experiment_key import StubSupervisedBinaryExperimentKey
from stubs.cl.runtime.experiments.stub_supervised_binary_trial import StubSupervisedBinaryTrial


@dataclass(slots=True, kw_only=True)
class StubSupervisedBinaryExperiment(StubSupervisedBinaryExperimentKey, SupervisedBinaryExperimentMixin[StubSupervisedBinaryExperimentKey, StubSupervisedBinaryTrial]):
    """Stub implementation of SupervisedBinaryExperimentMixin."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, do not restrict if not set)."""

    def get_key(self) -> StubSupervisedBinaryExperimentKey:
        return StubSupervisedBinaryExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    def create_trial(self) -> StubSupervisedBinaryTrial:
        return StubSupervisedBinaryTrial(
            experiment=self.get_key(),
            result=True,
            expected=True,
        ).build()
