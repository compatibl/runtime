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

import pytest
from matplotlib import pyplot as plt
from cl.runtime.plots.multi_plot import MultiPlot
from stubs.cl.runtime.plots.stub_heat_map_plots import StubHeatMapPlots
from cl.runtime.qa.regression_guard import RegressionGuard


def test_multi_heatmap(work_dir_fixture):
    """Test a multi heat map plot using RegressionGuard."""

    guard = RegressionGuard(ext="png", channel="test_multi_heat_map_plot.test_multi_heatmap")
    plot = MultiPlot(
        plot_id="test_multi_heat_map_plot.test_multi_heatmap",
        title="MultiPlot",
        plots=[
            StubHeatMapPlots.get_basic_plot("test"),
            StubHeatMapPlots.get_basic_plot("test"),
            StubHeatMapPlots.get_basic_plot("test"),
            StubHeatMapPlots.get_basic_plot("test"),
        ],
    ).build()
    fig = plot._create_figure()
    guard.write(fig)
    guard.verify()
    plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__])
