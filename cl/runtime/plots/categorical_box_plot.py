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
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class CategoricalBoxPlot(MatplotlibPlot):
    """A box plot comparing distributions across different categories"""

    title: str = required()
    """Plot title."""

    data: pd.DataFrame = required()  # TODO: Refactor to avoid using DataFrame as a field
    """DataFrame containing the data to plot. Must include columns specified by `x_col` and `y_col`."""

    x_col: str = required()
    """Name of the column in `data` to use for x-axis categories (e.g., 'persona', 'model_type')."""

    y_col: str = required()
    """Name of the column in `data` to use for y-axis values (e.g., 'confidence', 'score')."""

    x_order: List[str] = required()
    """Order of categories to display on the x-axis (e.g., ['expert', 'non_expert'])."""

    palette: Dict[str, str] = required()
    """Dictionary mapping category names (from `x_col`) to color specifications (e.g., hex codes, names)."""

    xlabel: Optional[str] = None
    """Label for the x-axis. If None, `x_col` name is used."""

    ylabel: Optional[str] = None
    """Label for the y-axis. If None, `y_col` name is used."""

    ylim: Optional[Tuple[Optional[float], ...]] = (None, None)
    """Tuple defining the y-axis limits (min, max). Use None for automatic limits. Default (None, None)."""

    box_width: float = 0.6
    """Width of the boxes in the plot. Default 0.6."""

    show_grid: bool = True
    """Whether to show the horizontal grid lines. Default True."""

    def _create_figure(self) -> plt.Figure:
        """Creates the Matplotlib figure for the categorical box plot."""

        fig, ax = plt.subplots(figsize=(7, 5))

        plot_data = self.data[self.data[self.x_col].isin(self.x_order)].copy()

        theme = self._get_pyplot_theme()

        with plt.style.context(theme):
            sns.boxplot(
                x=self.x_col,
                y=self.y_col,
                hue=self.x_col,
                data=plot_data,
                order=self.x_order,
                palette=self.palette,
                legend=False,
                ax=ax,
                width=self.box_width,
            )

            ax.set_title(self.title, fontsize=14, pad=15)
            ax.set_ylabel(self.ylabel if self.ylabel else self.y_col.replace("_", " ").title())
            ax.set_xlabel(self.xlabel if self.xlabel else self.x_col.replace("_", " ").title())

            if self.ylim != (None, None):
                ax.set_ylim(*self.ylim)

            if self.show_grid:
                ax.grid(axis="y", linestyle="--", alpha=0.7)
            else:
                ax.grid(False)

        fig.tight_layout()

        return fig
