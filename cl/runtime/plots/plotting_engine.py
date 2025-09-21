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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from cl.runtime.plots.plot import Plot
from cl.runtime.plots.plotting_engine_key import PlottingEngineKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class PlottingEngine(PlottingEngineKey, RecordMixin, ABC):
    """Base class for plot objects."""

    def get_key(self) -> PlottingEngineKey:
        return PlottingEngineKey(plotting_engine_id=self.plotting_engine_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if self.plotting_engine_id is None:
            # Use globally unique UUIDv7-based timestamp if not specified
            self.plotting_engine_id = Timestamp.create()

    @abstractmethod
    def render_html(self, plot: Plot) -> bytes:
        """Render the plot to HTML."""
