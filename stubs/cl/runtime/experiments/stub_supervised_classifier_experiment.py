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
from cl.runtime.experiments.classifier_experiment import ClassifierExperiment
from cl.runtime.experiments.supervised_classifier_experiment import SupervisedClassifierExperiment
from cl.runtime.experiments.supervised_classifier_trial import SupervisedClassifierTrial
from cl.runtime.experiments.trial import Trial


@dataclass(slots=True, kw_only=True)
class StubSupervisedClassifierExperiment(SupervisedClassifierExperiment):
    """Stub implementation of SupervisedClassifierExperiment."""

    def run_one(self) -> None:
        # Create a trial record with random result
        trial = SupervisedClassifierTrial(
            experiment=self.get_key(),
            label="abc",
            expected_label="def",
        ).build()
        DbContext.save_one(trial)
