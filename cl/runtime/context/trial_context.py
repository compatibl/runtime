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
from typing_extensions import Self
from cl.runtime.context.base_context import BaseContext
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class TrialContext(BaseContext):
    """Context for a single trial in an experiment."""

    trial_id: str | None = None
    """
    Trial identifier can be a single token or multiple tokens in backslash-delimited format.

    Notes:
      - Trial identifiers for the TrialContext stack are concatenated in the order entered
      - If trial field is None, it is is disregarded
    """

    @classmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """
        return "TrialContext"

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        # Get value from the current context
        previous = context.trial_id if (context := self.current_or_none()) is not None else None
        if not self.trial_id:
            # None or empty in this context, copy previous value
            self.trial_id = previous
        elif previous:
            # Both not None and not empty, combine using backslash separator
            self.trial_id = f"{previous}\\{self.trial_id}"

        # Return self to enable method chaining
        return self

    @classmethod
    def get_trial(cls) -> str:
        """Concatenates trial identifiers from the context stack, error if no current context or all are None."""
        if (result := cls.get_trial_or_none()) is not None:
            return result
        else:
            raise RuntimeError("Trial was not specified in TrialContext(...) or method invoked "
                               "outside the outermost 'with TrialContext(...)' clause.")

    @classmethod
    def get_trial_or_none(cls) -> str | None:
        """Concatenates trial identifiers from the context stack, returns None if no current context or all are None."""
        if (context := cls.current_or_none()) is not None and context.trial_id is not None:
            # Use the value from context if not None
            return context.trial_id
        else:
            # Otherwise return None
            return None
