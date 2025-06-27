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
from cl.runtime.experiments.experiment_type_key import ExperimentTypeKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.key_mixin import KeyMixin


@dataclass(slots=True)
class ExperimentKey(KeyMixin):
    """Abstract base class for a statistical experiment."""

    experiment_type: ExperimentTypeKey = required()
    """Experiment records are assigned to separate tables for each experiment type."""

    experiment_id: str = required()
    """Experiment identifier must be unique for each experiment type but not globally."""

    @classmethod
    def get_key_type(cls) -> type:
        return ExperimentKey

    def get_table(self) -> str:
        """Override the default to specify a custom table name based on experiment type."""
        return self.experiment_type.experiment_type_id
