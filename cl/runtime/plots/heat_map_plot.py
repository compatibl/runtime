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

import pandas as pd
import matplotlib.ticker as mticker
from dataclasses import dataclass
from typing import List
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from cl.runtime.plots.matrix_util import MatrixUtil
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.plots.matplotlib_util import MatplotlibUtil
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class HeatMapPlot(MatplotlibPlot):
    """Heat map visualization."""

    title: str = required()
    """Plot title."""

    row_labels: List[str] = required()
    """Row label for each cell in the same order of cells as other fields."""

    col_labels: List[str] = required()
    """Column label for each cell in the same order of cells as other fields."""

    received_values: List[float] = required()
    """Received value for each cell in the same order of cells as other fields."""

    expected_values: List[float] = required()
    """Expected (correct) value for each cell in the same order of cells as other fields."""

    x_label: str = required()
    """x-axis label."""

    y_label: str = required()
    """y-axis label."""

    def draw_to_axis(self, axes: plt.Axes) -> None:
        """Render relatively to axes of some plot."""
        theme = self._get_pyplot_theme()

        received_df, expected_df = (
            pd.DataFrame.from_records([values, self.col_labels, self.row_labels], index=["Value", "Col", "Row"])
            .T.pivot_table(index="Row", columns="Col", values="Value", sort=False)
            .astype(float)
            for values in [self.received_values, self.expected_values]
        )

        data = (received_df - expected_df).abs()

        cmap = LinearSegmentedColormap.from_list("rg", ["g", "y", "r"], N=256)

        with plt.style.context(theme):
            data = MatrixUtil.convert_confusion_matrix_to_percent(data)
            im = MatplotlibUtil.heatmap(
                data.values,
                data.index.tolist(),
                data.columns.tolist(),
                ax=axes,
                cmap=cmap
            )
            MatplotlibUtil.annotate_heatmap(
                im,
                labels=MatrixUtil.create_confusion_matrix_labels(data, in_percent=True),
                text_colors="black",
                size=6
            )
            cbar = plt.colorbar(im, ax=axes)
            cbar.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))  # adding percent sign to colorbar
            axes.set_title(self.title)
            axes.set_xlabel(self.x_label)
            axes.set_ylabel(self.y_label)

    def _create_figure(self) -> plt.Figure:
        """Render only this plot."""
        fig, axes = plt.subplots()
        self.draw_to_axis(axes)
        fig.tight_layout()
        return fig
