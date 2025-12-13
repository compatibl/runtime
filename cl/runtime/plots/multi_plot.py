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

import math
from dataclasses import dataclass
from typing import List
import numpy as np
from matplotlib import pyplot as plt
from cl.runtime.plots.matplotlib_plot import MatplotlibPlot
from cl.runtime.plots.plot import Plot
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class MultiPlot(MatplotlibPlot):
    """Visualization of multiple plots as a single one."""

    title: str = required()
    """Plot title."""

    plots: list[Plot] = required()
    """
    Plots to combine.
    Each Plot instance must implement draw_to_axis(ax) method to be successfully drawn.
    """

    def _create_figure(self) -> plt.Figure:
        theme = self._get_pyplot_theme()
        with plt.style.context(theme):
            n = len(self.plots)
            n_cols = math.ceil(math.sqrt(n))
            n_rows = math.ceil(n / n_cols)

            fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
            axes = np.array(axes).reshape(-1)

            for plot, ax in zip(self.plots, axes):
                if hasattr(plot, "draw_to_axis"):
                    plot.draw_to_axis(ax)
                else:
                    raise TypeError(f"Plot {plot.__class__.__name__} does not support draw_to_axis(ax).")

            for j in range(len(self.plots), len(axes)):
                fig.delaxes(axes[j])

            fig.suptitle(self.title)
            fig.tight_layout()

            return fig
