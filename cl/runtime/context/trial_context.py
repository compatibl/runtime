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
from typing import Type
from cl.runtime.context.base_context import BaseContext
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class TrialContext(BaseContext):
    """Context for a single trial in an experiment."""

    trial_id: str | None = None
    """Trial identifier specified by this context, or None if not running a trial."""

    def __post_init__(self):
        """Combine with the value from the previous trial context using dot delimiter."""

        # Do not execute this code on deserialized context instances (e.g. when they are passed to a task queue)
        if not self.is_deserialized:

            # Combine with the previous trial_id if set
            if (prev_context := TrialContext.current_or_none()) is not None and prev_context.trial_id is not None:
                if self.trial_id is not None:
                    self.trial_id = f"{prev_context.trial_id}.{self.trial_id}"
                else:
                    self.trial_id = prev_context.trial_id

    
    @classmethod
    def get_key_type(cls) -> Type:
        """
        The lookup of current context for cls will be done using the type returned by this method as key.

        Notes:
            - Return as specific type rather than type(self) to avoid variation across derived types
            - The returned type may be a base context class or a dedicated key type
            - Contexts that have different key types are isolated from each other and have independent 'with' clauses
            - As all contexts are singletons and have no key fields, get_key method is not required
        """

