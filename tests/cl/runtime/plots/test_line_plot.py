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
from cl.runtime.qa.regression_guard import RegressionGuard
from stubs.cl.runtime.plots.stub_line_plots import StubLinePlots


def test_one_line(work_dir_fixture):
    """Test LinePlot with one line using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(ext="png", prefix="test_line_plot.test_one_line").build()

    # Arrange: Generate plot
    plot = StubLinePlots.get_one_line_plot(plot_id="test_line_plot.test_one_line")

    # Act: Write plot to regression guard
    guard.write(plot.get_png())

    # Assert: Verify plot
    guard.verify()


def test_two_line(work_dir_fixture):
    """Test LinePlot with two lines using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(ext="png", prefix="test_line_plot.test_two_line").build()

    # Arrange: Generate plot
    plot = StubLinePlots.get_two_line_plot(plot_id="test_line_plot.test_two_line")

    # Act: Write plot to regression guard
    guard.write(plot.get_png())

    # Assert: Verify plot
    guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
