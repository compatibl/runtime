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
from stubs.cl.runtime.plots.stub_stack_bar_plots import StubStackBarPlots


def test_single_stack(work_dir_fixture):
    """Test stacked bar plot with single stack using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(ext="png", channel="test_stack_bar_plot.stack_bar_plot")

    # Arrange: Generate the plot
    plot = StubStackBarPlots.get_single_stack_plot("test_stack_bar_plot.stack_bar_plot")

    # Act: Write plot to regression guard
    guard.write(plot.get_png())

    # Assert: Verify plot
    guard.verify()


def test_4_groups_2_bars(work_dir_fixture):
    """Test StackBarPlot with 4 stacks with 2 bars each using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(ext="png", channel="test_stack_bar_plot.test_4_stacks_2_bars")

    # Arrange: Generate plot
    plot = StubStackBarPlots.get_4_stacks_2_bars_plot("test_stack_bar_plot.test_4_stacks_2_bars")

    # Act: Write plot to regression guard
    guard.write(plot.get_png())

    # Assert: Verify plot
    guard.verify()


def test_4_stacks_5_bars(work_dir_fixture):
    """Test GroupBarPlot plot with 4 groups and 5 bars using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(ext="png", channel="test_stack_bar_plot.test_4_stacks_5_bars")

    # Arrange: Generate plot
    plot = StubStackBarPlots.get_4_stacks_5_bars("test_stack_bar_plot.test_4_stacks_5_bars")

    # Act: Write plot to regression guard
    guard.write(plot.get_png())

    # Assert: Verify plot
    guard.verify()


if __name__ == "__main__":
    pytest.main([__file__])
