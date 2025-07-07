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
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from cl.runtime.plots.bar_plot import BarPlot

# Color map for confusion matrix labels stack bar plot.
color_map = {
    "TP": "#66bb66",
    "TN": "#228B22",
    "FP": "#ff6666",
    "FN": "#b22222",
}


@dataclass(slots=True, kw_only=True)
class StackBarPlot(BarPlot):
    """Base class for the 2D stack bar plot."""

    def _create_figure(self) -> plt.Figure:

        data = (
            pd.DataFrame.from_records([self.values, self.bar_labels, self.group_labels], index=["Value", "Col", "Row"])
            .T.pivot_table(index="Row", columns="Col", values="Value", sort=False)
            .astype(float)
        )

        fig, axes, x_ticks = self._prepare_common_plot_elements(data)

        bottom = np.zeros(len(x_ticks))
        default_colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

        for i, col in enumerate(data.columns):
            color = color_map.get(col, None)
            if color is None:
                if col.startswith("True"):
                    color = "green"
                elif col.startswith("False"):
                    color = "red"
                else:
                    color = default_colors[i % len(default_colors)]

            values = data[col].values
            axes.bar(x_ticks, values, bottom=bottom, label=col, color=color)
            bottom += values
        axes.legend()
        return fig
