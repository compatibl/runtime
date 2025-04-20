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
from stubs.cl.runtime.plots.stub_line_plots import StubLinePlots


def test_one_line(pytest_work_dir):
    StubLinePlots.get_one_line_plot(plot_id="line_plot.test_one_line").save_png()


def test_two_lines(pytest_work_dir):
    StubLinePlots.get_two_line_plot(plot_id="line_plot.test_two_line").save_png()


if __name__ == "__main__":
    pytest.main([__file__])
