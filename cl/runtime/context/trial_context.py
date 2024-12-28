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

from typing_extensions import Self

from cl.runtime.context.base_context import BaseContext
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class TrialContext(BaseContext):
    """Context for a single trial in an experiment."""

    trial: TrialKey | None = None
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

    @classmethod
    def get_trial_or_none(cls) -> TrialKey | None:
        """Concatenates trial identifiers from the context stack, returns None if no current context or all are None."""
        if (context_stack := cls.get_context_stack()) is not None:
            # Gather those trial keys that are not None
            trial_keys = [trial for context in context_stack if (trial := context.trial) is not None]
            # Consider the possibility that after removing tokens that are None, the list becomes empty
            if trial_keys:
                # Concatenate
                trial_id = "\\".join([trial_key.trial_id for trial_key in trial_keys])
                return TrialKey(trial_id=trial_id)
            else:
                return None
        else:
            # If not defined, return None
            return None

    @classmethod
    def get_trial(cls) -> TrialKey:
        """Concatenates trial identifiers from the context stack, error if no current context or all are None."""
        if (result := cls.get_trial_or_none()) is not None:
            return result
        else:
            raise RuntimeError("Trial is not specified or method invoked outside the outermost 'with' clause.")
