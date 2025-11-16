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
from cl.runtime.stat.case_key import CaseKey
from cl.runtime.stat.classifier_experiment import ClassifierExperiment
from cl.runtime.stat.classifier_trial import ClassifierTrial


@dataclass(slots=True, kw_only=True)
class StubClassifierExperiment(ClassifierExperiment):
    """Stub implementation of ClassifierExperiment."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

    def create_trial(self, condition: CaseKey) -> ClassifierTrial:
        label = random.choice(self.class_labels)
        return ClassifierTrial(
            experiment=self.get_key(),
            param=condition,
            label=label,
        ).build()
