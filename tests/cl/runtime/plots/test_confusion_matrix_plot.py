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
from pathlib import Path
import pandas as pd
from cl.runtime.context.testing_context import TestingContext
from cl.runtime.plots.confusion_matrix_plot import ConfusionMatrixPlot
from cl.runtime.plots.confusion_matrix_plot_style import ConfusionMatrixPlotStyle
from cl.runtime.testing.pytest.pytest_fixtures import local_dir_fixture


def test_smoke(local_dir_fixture):
    raw_data = pd.read_csv(Path(__file__).resolve().parent / "./test_confusion_matrix_plot.csv")

    with TestingContext() as context:
        matrix_plot = ConfusionMatrixPlot()
        matrix_plot.title = "Confusion Matrix"
        matrix_plot.expected_categories = raw_data["True Category"].values.tolist()
        matrix_plot.received_categories = raw_data["Predicted"].values.tolist()

        fig = matrix_plot.create_figure()
    fig.savefig("test_confusion_matrix_plot.test_smoke.png")


def test_smoke_dark_theme(local_dir_fixture):
    raw_data = pd.read_csv(Path(__file__).resolve().parent / "./test_confusion_matrix_plot.csv")

    with TestingContext() as context:
        matrix_plot_style = ConfusionMatrixPlotStyle()
        matrix_plot_style.dark_theme = True

        matrix_plot = ConfusionMatrixPlot()
        matrix_plot.title = "Confusion Matrix"
        matrix_plot.expected_categories = raw_data["True Category"].values.tolist()
        matrix_plot.received_categories = raw_data["Predicted"].values.tolist()
        matrix_plot.style = matrix_plot_style

        fig = matrix_plot.create_figure()
    fig.savefig("test_confusion_matrix_plot.test_smoke_dark_theme.png")


if __name__ == "__main__":
    pytest.main([__file__])
