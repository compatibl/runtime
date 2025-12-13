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
from typing import Tuple
import numpy as np
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class LinePlot(MatplotlibPlot):
    """Class for creating a 2D line plot using Matplotlib."""

    title: str = required()
    """Plot title."""

    x_values: list[float] = required()
    """List of X-coordinates, common for all lines."""

    lines: dict[str, list[float]] = required()
    """Dictionary mapping line labels (str) to lists of Y-coordinates (list[float]).
       The order of Y-values must correspond to the order of x_values.
       NaN values in Y-coordinates will create gaps in the lines."""

    line_options: dict[str, dict[str, str]] | None = None
    """Optional dictionary mapping line labels to their specific plotting options
       (e.g., {'color': 'red', 'marker': 'x', 'linestyle': '--'}). Keys in the inner
       dictionary correspond to matplotlib.pyplot.plot arguments."""

    x_axis_label: str | None = None
    """X-axis label."""

    y_axis_label: str | None = None
    """Y-axis label."""

    y_lim: tuple[float | None, ...] | None = None
    """Y-axis limits (min, max). Set elements to None for autoscaling respective end."""

    figsize: tuple[float, ...] = (10, 6)
    """Figure size in inches (width, height)."""

    grid: bool = True
    """Whether to display grid lines."""

    def _create_figure(self) -> plt.Figure:
        # Load style object or create with default settings if not specified
        theme = self._get_pyplot_theme()

        default_marker_cycle = ["o", "x", "s", "^", "v", "d", "<", ">"]

        with plt.style.context(theme):
            fig = plt.figure(figsize=self.figsize)
            axes = fig.add_subplot()

            line_num = 0
            for label, y_values in self.lines.items():
                plot_kwargs = {"label": label}

                specific_options = self.line_options.get(label, {}) if self.line_options else {}
                plot_kwargs.update(specific_options)

                if "marker" not in plot_kwargs:
                    if len(self.lines) > 1:
                        plot_kwargs["marker"] = default_marker_cycle[line_num % len(default_marker_cycle)]

                y_values_np = np.array(y_values, dtype=float)
                axes.plot(self.x_values, y_values_np, **plot_kwargs)
                line_num += 1

            if self.x_axis_label:
                axes.set_xlabel(self.x_axis_label)
            if self.y_axis_label:
                axes.set_ylabel(self.y_axis_label)
            axes.set_title(self.title)

            axes.set_xticks(self.x_values)

            if self.y_lim is not None:
                current_ylim = axes.get_ylim()
                final_ylim = (
                    self.y_lim[0] if self.y_lim[0] is not None else current_ylim[0],
                    self.y_lim[1] if self.y_lim[1] is not None else current_ylim[1],
                )
                axes.set_ylim(*final_ylim)

            if self.grid:
                axes.grid(True, which="both", linestyle="--", linewidth=0.5)

            axes.legend()

        return fig
