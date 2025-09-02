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
from cl.runtime.db.query_mixin import QueryMixin
from cl.runtime.records.conditions import Condition
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.stats.experiment_key import ExperimentKey
from cl.runtime.stats.trial_key import TrialKey


@dataclass(slots=True, kw_only=True)
class TrialKeyQuery(DataclassMixin, QueryMixin):
    """Query for TrialKey by the experiment and timestamp fields."""

    experiment: ExperimentKey = required()
    """Experiment for which the trial is performed."""

    timestamp: str | Condition[str] | None = None  # TODO: Use UUID based timestamp for faster range queries
    """Trial timestamp must be unique for each experiment but not globally."""

    def get_target_type(self) -> type[KeyMixin]:
        return TrialKey
