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
from typing import Tuple
from cl.runtime.contexts.context import Context
from cl.runtime.primitive.primitive_serializers import PrimitiveSerializers
from cl.runtime.records.protocols import TPrimitive, is_sequence, is_primitive, PRIMITIVE_CLASS_NAMES
from cl.runtime.records.type_util import TypeUtil


@dataclass(slots=True, kw_only=True)
class TrialContext(Context):
    """Context for a single trial in an experiment."""

    trial_chain: Tuple[str, ...]
    """Tuple of trial identifiers in the trial context stack."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        if not self.trial_chain:
            raise RuntimeError("TrialContext is created with an empty trial chain. Use TrialContext.create(token)\n"
                               "method where token is an instance of a primitive type to create.")

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
    def create(cls, token: TPrimitive):
        """Combine the specified token with the current chain and return a new context instance."""

        # Allow only primitive types for tokens
        if token is not None and is_primitive(token):

            # Serialize the trial identifier
            serialized_id = PrimitiveSerializers.DEFAULT.serialize(token)

            # Get trial chain from the current context
            previous_chain = context.trial_chain if (context := cls.current_or_none()) is not None else None

            if previous_chain:
                # Combine the previous chain and the new identifier
                return TrialContext(trial_chain=tuple([x for x in previous_chain] + [serialized_id])).build()
            else:
                # Previous chain is empty, use the new trial identifier as the chain
                return TrialContext(trial_chain=(serialized_id,)).build()
        else:
            primitive_class_names = ", ".join(PRIMITIVE_CLASS_NAMES)
            raise RuntimeError(f"The argument of TrialContext.create must be one of the following primitive classes:\n"
                               f"{primitive_class_names}\nThe class {TypeUtil.name(token)} is not supported.")

    @classmethod
    def get_trial(cls) -> str:
        """Concatenates trial identifiers from the context stack, error if no current context or all are None."""
        if (result := cls.get_trial_or_none()) is not None:
            return result
        else:
            raise RuntimeError(
                "Method is invoked outside the outermost 'with TrialContext.create(...)' clause."
            )

    @classmethod
    def get_trial_or_none(cls) -> str | None:
        """Concatenates trial identifiers from the context stack, returns None if no current context or all are None."""
        if (context := cls.current_or_none()) is not None and context.trial_chain:
            # Concatenate trial chain tokens from the current context if not None or empty
            return "\\".join(context.trial_chain)
        else:
            # Otherwise return None
            return None
