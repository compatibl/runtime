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

import random
from dataclasses import dataclass
from cl.runtime.stats.experiment_scenario_key import ExperimentScenarioKey
from cl.runtime.stats.supervised_binary_experiment import SupervisedBinaryExperiment
from cl.runtime.stats.supervised_binary_trial import SupervisedBinaryTrial


@dataclass(slots=True, kw_only=True)
class StubSupervisedBinaryExperiment(SupervisedBinaryExperiment):
    """Stub implementation of SupervisedBinaryExperiment."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    def create_trial(self, scenario: ExperimentScenarioKey) -> SupervisedBinaryTrial:
        actual = random.choice([True, False])
        expected = random.choice([True, False])
        return SupervisedBinaryTrial(
            experiment=self.get_key(), actual=actual, expected=expected, scenario=scenario
        ).build()
