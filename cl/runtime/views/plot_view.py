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
from typing import Self
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.plots.plot_key import PlotKey
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_key
from cl.runtime.views.view import View


@dataclass(slots=True, kw_only=True)
class PlotView(View):
    """Plot record or key."""

    plot: PlotKey = required()
    """Plot record or key."""

    def materialize(self) -> Self:
        """Return Self with loaded plot if self.plot is a key."""

        if is_key(type(self.plot)):
            plot = active(DataSource).load_one(self.plot)
            self.plot = plot

        return self
