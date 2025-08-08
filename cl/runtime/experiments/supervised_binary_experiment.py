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
from cl.runtime.experiments.binary_experiment import BinaryExperiment
from cl.runtime.experiments.supervised_binary_trial import SupervisedBinaryTrial
from cl.runtime.experiments.trial_key_query import TrialKeyQuery
from cl.runtime.plots.stack_bar_plot import StackBarPlot


@dataclass(slots=True, kw_only=True)
class SupervisedBinaryExperiment(BinaryExperiment, ABC):
    """Supervised binary experiment with boolean actual and expected result types."""

    def get_plot(self, plot_id: str) -> StackBarPlot:
        """Builds and returns plot for Supervised Binary Experiment."""
        if not self.scenarios:
            raise RuntimeError("Experiment must have scenarios to build a plot.")

        group_labels = []
        bar_labels = []
        values = []
        trial_query = TrialKeyQuery(experiment=self.get_key()).build()
        all_trials = active(DataSource).load_where(trial_query, cast_to=SupervisedBinaryTrial)

        for scenario in self.scenarios:
            trials = self.get_scenario_trials(all_trials, scenario)
            total = len(trials)

            tp = tn = fp = fn = 0

            for trial in trials:
                if trial.actual and trial.expected:
                    tp += 1
                elif not trial.actual and not trial.expected:
                    tn += 1
                elif trial.actual and not trial.expected:
                    fp += 1
                elif not trial.actual and trial.expected:
                    fn += 1

            group_labels.extend([scenario.experiment_scenario_id] * 4)
            bar_labels.extend(["TP", "TN", "FP", "FN"])
            values.extend(
                [
                    tp / total,
                    tn / total,
                    fp / total,
                    fn / total,
                ]
            )

        result = StackBarPlot(
            plot_id=plot_id,
            title="Classification Outcome Ratios by Scenario",
            value_axis_label="Ratio",
            xtick_rotation=45,
            xtick_ha="right",
            value_ticks=[0.0, 0.5, 1.0],
        )
        result.group_labels = group_labels
        result.bar_labels = bar_labels

        result.values = values
        return result.build()
