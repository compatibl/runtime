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
from cl.runtime.experiments.classifier_experiment_mixin import ClassifierExperimentMixin
from stubs.cl.runtime.experiments.stub_classifier_experiment_key import StubClassifierExperimentKey
from stubs.cl.runtime.experiments.stub_classifier_trial import StubClassifierTrial


@dataclass(slots=True, kw_only=True)
class StubClassifierExperiment(StubClassifierExperimentKey, ClassifierExperimentMixin[StubClassifierExperimentKey, StubClassifierTrial]):
    """Stub implementation of ClassifierExperimentMixin."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, do not restrict if not set)."""

    def get_key(self) -> StubClassifierExperimentKey:
        return StubClassifierExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    def create_trial(self) -> StubClassifierTrial:
        return StubClassifierTrial(
            experiment=self.get_key(),
            result="A",
        ).build()
