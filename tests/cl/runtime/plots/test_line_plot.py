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
from stubs.cl.runtime.plots.stub_line_plots import StubLinePlots
from cl.runtime.qa.regression_guard import RegressionGuard


def test_one_line(work_dir_fixture):
    """Test LinePlot with one line using RegressionGuard."""

    guard = RegressionGuard(ext="png", channel="test_line_plot.test_one_line")
    plot = StubLinePlots.get_one_line_plot(plot_id="test_line_plot.test_one_line")
    fig = plot._create_figure()
    guard.write(fig)
    guard.verify()
    plt.close(fig)


def test_two_line(work_dir_fixture):
    """Test LinePlot with two lines using RegressionGuard."""

    guard = RegressionGuard(ext="png", channel="test_line_plot.test_two_line")
    plot = StubLinePlots.get_two_line_plot(plot_id="test_line_plot.test_two_line")
    fig = plot._create_figure()
    guard.write(fig)
    guard.verify()
    plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__])
