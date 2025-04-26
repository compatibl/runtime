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
from cl.runtime.qa.pytest.pytest_fixtures import pytest_work_dir  # noqa
from stubs.cl.runtime.plots.stub_group_bar_plots import StubGroupBarPlots


def test_single_group(pytest_work_dir):
    """Test GroupBarPlot with one group."""
    StubGroupBarPlots.get_single_group_plot("test_group_bar_plot.group_bar_plot").save_png()


@pytest.mark.skip("Restore test when it becomes possible to override the default theme.")
def test_dark_theme(pytest_work_dir):
    """Test GroupBarPlot plot in dark mode."""


def test_4_groups_2_bars(pytest_work_dir):
    """Test GroupBarPlot with 4 groups with 2 bars each."""
    StubGroupBarPlots.get_4_groups_2_bars_plot("test_group_bar_plot.test_4_groups_2_bars").save_png()


def test_4_groups_5_bars(pytest_work_dir):
    """Test GroupBarPlot plot with 4 groups and 5 bars."""
    StubGroupBarPlots.get_4_groups_5_bars("test_group_bar_plot.test_4_groups_5_bars").save_png()


if __name__ == "__main__":
    pytest.main([__file__])
