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
import numpy as np
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.params.param import Param
from cl.runtime.plots.heat_map_plot import HeatMapPlot
from cl.runtime.plots.multi_plot import MultiPlot
from cl.runtime.records.key_util import KeyUtil
from cl.runtime.stat.classifier_experiment import ClassifierExperiment
from cl.runtime.stat.supervised_classifier_trial import SupervisedClassifierTrial
from cl.runtime.stat.trial_query import TrialQuery


@dataclass(slots=True, kw_only=True)
class SupervisedClassifierExperiment(ClassifierExperiment, ABC):
    """Supervised classifier experiment with string actual and expected results representing the class label."""

    def get_plot(self, plot_id: str) -> MultiPlot:
        if not self.params:
            raise RuntimeError(
                "Experiment must have one or more condition to build a plot."
            )  # TODO: Support no conditions

        plots = []
        num_labels = len(self.class_labels)

        # Get trials for all conditions
        trial_query = TrialQuery(experiment=self.get_key()).build()
        all_trials = active(DataSource).load_by_query(trial_query, cast_to=SupervisedClassifierTrial)

        params = active(DataSource).load_many(self.params, cast_to=Param)
        for param in params:
            # Get trials for the condition
            trials = tuple(trial for trial in all_trials if KeyUtil.is_equal(trial.param, param))

            y_true = [trial.label for trial in trials]
            y_pred = [trial.expected_label for trial in trials]

            matrix = np.zeros((num_labels, num_labels), dtype=int)
            label_to_index = {label: i for i, label in enumerate(self.class_labels)}

            for true, pred in zip(y_true, y_pred):
                i = label_to_index[true]
                j = label_to_index[pred]
                matrix[i, j] += 1

            row_labels = np.repeat(self.class_labels, len(self.class_labels)).tolist()
            col_labels = self.class_labels * num_labels
            received_values = matrix.flatten().tolist()
            expected_values = [0.0] * len(received_values)

            heatmap = HeatMapPlot(
                plot_id=f"{plot_id}_{param.label}",
                title=f"{param.label}",
                row_labels=row_labels,
                col_labels=col_labels,
                received_values=received_values,
                expected_values=expected_values,
                x_label="Predicted label",
                y_label="True label",
            )

            plots.append(heatmap)

        result = MultiPlot(plot_id=plot_id, title=plot_id, plots=plots).build()
        return result
