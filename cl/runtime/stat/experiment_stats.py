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
from cl.runtime.primitive.float_util import FloatUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.stat.experiment_stats_key import ExperimentStatsKey
from cl.runtime.stat.experiment_stats_view import ExperimentStatsView


@dataclass(slots=True, kw_only=True)
class ExperimentStats(ExperimentStatsKey, RecordMixin):
    """Representation of aggregated statistics from an experiment run."""

    retry_count: int | None = None
    """Number of retries."""

    time_per_trial: float | None = None
    """Average time per trial in seconds."""

    total_time: float | None = None
    """Total execution time of the experiment in seconds."""

    def get_key(self) -> ExperimentStatsKey:
        return ExperimentStatsKey(experiment=self.experiment).build()

    def get_view(self) -> ExperimentStatsView:
        """Build a view to display statistics as a table in UI."""

        return ExperimentStatsView(
            retry_count=self.retry_count,
            time_per_trial_sec=FloatUtil.round(self.time_per_trial) if self.time_per_trial else None,
            total_time_sec=FloatUtil.round(self.total_time) if self.total_time else None,
        ).build()
