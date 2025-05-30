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
from cl.runtime.experiments.binary_experiment import BinaryExperiment
from cl.runtime.experiments.binary_experiment_mixin import BinaryExperimentMixin
from cl.runtime.experiments.binary_trial import BinaryTrial
from stubs.cl.runtime.experiments.stub_binary_experiment_key import StubBinaryExperimentKey
from stubs.cl.runtime.experiments.stub_binary_trial import StubBinaryTrial


@dataclass(slots=True, kw_only=True)
class StubBinaryExperiment(StubBinaryExperimentKey, BinaryExperimentMixin[StubBinaryExperimentKey, StubBinaryTrial]):
    """Stub implementation of BinaryExperimentMixin."""

    max_trials: int | None = None
    """Maximum number of trials to run (optional)."""

    max_parallel: int | None = None
    """Maximum number of trials to run in parallel (optional, do not restrict if not set)."""

    def get_key(self) -> StubBinaryExperimentKey:
        return StubBinaryExperimentKey(experiment_id=self.experiment_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    def create_trial(self) -> StubBinaryTrial:
        return StubBinaryTrial(experiment=self.get_key(), result=True).build()
