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
from cl.runtime.experiments.experiment_kind_key import ExperimentKindKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin


@dataclass(slots=True)
class ExperimentScenarioKey(KeyMixin):
    """One of multiple scenarios for an experiment."""

    experiment_kind: ExperimentKindKey = required()
    """Experiment scenarios are separated by experiment kind."""

    experiment_scenario_id: str = required()
    """Unique experiment scenario identifier."""

    @classmethod
    def get_key_type(cls) -> type[KeyMixin]:
        return ExperimentScenarioKey
