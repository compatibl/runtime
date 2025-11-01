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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.plots.stack_bar_plot import StackBarPlot
from cl.runtime.stats.binary_trial import BinaryTrial
from cl.runtime.stats.experiment import Experiment
from cl.runtime.stats.trial_query import TrialQuery


@dataclass(slots=True, kw_only=True)
class BinaryExperiment(Experiment, ABC):
    """Unsupervised binary experiment with boolean result type."""

    def get_plot(self, plot_id: str) -> StackBarPlot:
        """Builds and returns plot for Binary Experiment."""

        if not self.scenarios:
            raise RuntimeError("Experiment must have scenarios to build a plot.")

        group_labels = []
        bar_labels = []
        values = []
        trial_query = TrialQuery(experiment=self.get_key()).build()
        all_trials = active(DataSource).load_by_query(trial_query, cast_to=BinaryTrial)

        for scenario in self.scenarios:

            trials = self.get_scenario_trials(all_trials, scenario)
            total = len(trials)

            true_trials = sum(trial.outcome for trial in trials)
            false_trials = total - true_trials

            group_labels.extend([scenario.experiment_scenario_id] * 2)
            bar_labels.extend(["True", "False"])
            values.extend([true_trials / total, false_trials / total])

        result = StackBarPlot(
            plot_id=plot_id,
            title="True/False Ratio by Scenario",
            value_axis_label="Ratio",
            xtick_rotation=45,
            xtick_ha="right",
            value_ticks=[0.0, 0.5, 1.0],
        )
        result.bar_labels = bar_labels
        result.group_labels = group_labels
        result.values = values
        return result.build()
