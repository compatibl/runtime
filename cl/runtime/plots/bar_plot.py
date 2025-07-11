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
from typing import List
import numpy as np
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class BarPlot(MatplotlibPlot, ABC):
    """Base class for the 2D bar plot."""

    title: str = required()
    """Plot title."""

    bar_labels: List[str] = required()
    """List of bar labels."""

    group_labels: List[str] = required()
    """List of group labels."""

    values: List[float] = required()
    """List of values in the same order as bar and group labels."""

    bar_axis_label: str | None = None
    """Bar axis label."""

    value_axis_label: str | None = None
    """Value axis label."""

    value_ticks: List[float] | None = None
    """Custom ticks for the value axis."""

    xtick_rotation: float = 0.0
    """Rotation angle for x-axis tick labels (degrees). Default is 0 (horizontal)."""

    xtick_ha: str = "center"
    """Horizontal alignment for rotated x-axis tick labels ('center', 'right', 'left').
       Usually 'right' for positive rotation (e.g., 45), 'center' for 0/90."""

    def _prepare_common_plot_elements(self, data) -> tuple[plt.Figure, plt.Axes, np.ndarray]:
        """
        Sets up the figure and axes with shared logic for child bar plots.
        Returns: (fig, axes, x_ticks)
        """

        theme = self._get_pyplot_theme()

        with plt.style.context(theme):
            fig = plt.figure()
            axes = fig.add_subplot()

            x_ticks = np.arange(len(data.index))
            axes.set_xticks(x_ticks, data.index.tolist())

            if self.xtick_rotation != 0.0:
                plt.setp(axes.get_xticklabels(), rotation=self.xtick_rotation, ha=self.xtick_ha)

            if self.value_ticks is not None:
                axes.set_yticks(self.value_ticks)

            if data.min().min() < 0:
                axes.axhline(0, color="grey", linestyle="--", linewidth=0.8, zorder=1)

            axes.set_xlabel(self.bar_axis_label or "")
            axes.set_ylabel(self.value_axis_label or "")
            axes.set_title(self.title)
            fig.tight_layout()

        return fig, axes, x_ticks
