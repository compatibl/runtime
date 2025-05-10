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

from abc import ABC
from dataclasses import dataclass
from cl.runtime.experiments.experiment_key import ExperimentKey
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.conditions import Condition
from cl.runtime.records.for_dataclasses.query import Query
from cl.runtime.records.query_mixin import QueryMixin


@dataclass(slots=True, kw_only=True)
class TrialQuery(Query, QueryMixin[TrialKey], ABC):
    """Query for a trial of an experiment."""

    timestamp: Condition[Timestamp] | None = None
    """Unique trial timestamp."""

    experiment: Condition[ExperimentKey] | None = None
    """Experiment for which the trial is recorded."""
