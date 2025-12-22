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
from stubs.cl.runtime.plots.stub_heat_map_plots import StubHeatMapPlots


def test_basic(work_dir_fixture):
    """Test a basic heat map plot using RegressionGuard."""

    # Create regression guard
    guard = RegressionGuard(channel="test_heat_map_plot.test_basic")

    # Arrange: Generate plot
    plot = StubHeatMapPlots.get_basic_plot("test_heat_map_plot.test_basic")

    # Act: Write plot to regression guard
    guard.write(plot)

    # Assert: Verify plot
    guard.verify()


@pytest.mark.skip("Restore test when it becomes possible to override the default theme.")
def test_dark_theme(work_dir_fixture):
    pass


if __name__ == "__main__":
    pytest.main([__file__])
