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
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_empty
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.stat.draw_key import DrawKey


@dataclass(slots=True, kw_only=True)
class Draw(DrawKey, RecordMixin):
    """Keep track of a unique draw identifier consisting of dot-delimited draw indices for each nested draw context."""

    draw_index: int = required()
    """Zero-based draw index for this trial is the last token of draw_id."""

    def get_key(self) -> DrawKey:
        return DrawKey(draw_id=self.draw_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Verify that draw index is a non-negative int
        if is_empty(self.draw_index):
            RuntimeError(f"Draw index is None or an empty primitive type.")
        elif not isinstance(self.draw_index, int):
            raise RuntimeError(f"Draw index '{self.draw_index}' is not an int.")
        elif self.draw_index < 0:
            raise RuntimeError(f"Draw index is negative.")

        # Unique draw identifier consists of dot-delimited draw indices for each nested draw context
        if current_draw := active_or_none(type(self)):
            # Combine the active draw_id with self.draw_index
            self.draw_id = f"{current_draw.draw_id}.{self.draw_index}"
        else:
            # No active draw_id, convert to string
            self.draw_id = str(self.draw_index)
