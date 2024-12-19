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
    """
    Trial identifier specified by this context. 
    
    Notes:
      - Because 'with' clause cannot be under if/else, in some cases trial_id may be conditionally None
        but 'with TrialContext(...)' clause would still be present.
      - If trial_id is None, this TrialContext is disregarded
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
    def get_trial_id(cls) -> str | None:
        """
        Unique trial identifier in backslash-delimited format obtained by concatenating identifiers from
        the TrialContext stack in the order entered, or None outside 'with TrialContext(...)' clause.

        Notes:
          - Because 'with' clause cannot be under if/else, in some cases trial_id may be conditionally None
            but 'with TrialContext(...)' clause would still be present.
          - If trial_id is None, the corresponding TrialContext is disregarded
          - If trial_id is None for the entire the TrialContext stack, this method returns None
        """
        if cls.current_or_none() is not None:
            # Gather those tokens from the context stack that are not None
            tokens = [trial_id for context in cls._get_context_stack() if (trial_id := context.trial_id) is not None]
            # Consider the possibility that after removing tokens that are None, the list becomes empty
            if tokens:
                return "\\".join(tokens)  # Concatenate
            else:
                return None
        else:
            return None
