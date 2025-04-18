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
from typing import List
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class GroupBarPlot(MatplotlibPlot):
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

    xtick_ha: str = 'center'
    """Horizontal alignment for rotated x-axis tick labels ('center', 'right', 'left').
       Usually 'right' for positive rotation (e.g., 45), 'center' for 0/90."""

    def _create_figure(self) -> plt.Figure:
        # Load style object or create with default settings if not specified
        theme = self._get_pyplot_theme()

        data = (
            pd.DataFrame.from_records([self.values, self.bar_labels, self.group_labels], index=["Value", "Col", "Row"])
            .T.pivot_table(index="Row", columns="Col", values="Value", sort=False)
            .astype(float)
        )

        with plt.style.context(theme):
            fig = plt.figure()
            axes = fig.add_subplot()

            num_groups = data.shape[0]
            num_bars = data.shape[1]

            x_ticks = np.arange(num_groups)

            if num_bars % 2 != 0:
                bar_shifts_positive = list(range(1, num_bars // 2 + 1))
            else:
                bar_shifts_positive = [x + 1 / 2 for x in range(num_bars // 2)]

            bar_shifts = [-x for x in reversed(bar_shifts_positive)]

            if num_bars % 2 != 0:
                bar_shifts += [0]

            bar_shifts += bar_shifts_positive

            space = 1 / (num_bars + 1)

            for i, (bar_label, bar_shift) in enumerate(zip(data.columns, bar_shifts)):
                axes.bar(x_ticks + space * bar_shift, data[bar_label].values, space, label=bar_label)

            axes.set_xticks(x_ticks, data.index.tolist())

            if self.xtick_rotation != 0.0:
                plt.setp(axes.get_xticklabels(), rotation=self.xtick_rotation, ha=self.xtick_ha)

            if self.value_ticks is not None:
                axes.set_yticks(self.value_ticks)

            min_value_in_plot = data.min().min()
            if min_value_in_plot < 0:
                axes.axhline(0, color='grey', linestyle='--', linewidth=0.8, zorder=1)

            # Set figure and axes labels
            axes.set_xlabel(self.bar_axis_label)
            axes.set_ylabel(self.value_axis_label)
            axes.set_title(self.title)

            # Add legend
            axes.legend()

        return fig
