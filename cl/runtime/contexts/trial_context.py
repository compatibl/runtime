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
from typing import Iterable
from typing import Self
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.protocols import PRIMITIVE_CLASS_NAMES
from cl.runtime.records.protocols import TPrimitive
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers


@dataclass(slots=True, kw_only=True)
class TrialContext(DataMixin):
    """Context for a trial in an experiment."""

    trial_chain: tuple[str, ...]
    """Tuple of trial identifiers in the trial context stack."""

    @classmethod
    def get_base_type(cls) -> type:
        return TrialContext

    @classmethod
    def append_token(cls, token: TPrimitive | None) -> Self:
        """
        Combine the specified token with the current chain and return a new context instance.
        To make it easier to implement conditionally adding a token, the argument can be None
        to indicate that the current chain should not be modified.
        """
        return cls.append_tokens((token,))

    @classmethod
    def append_tokens(cls, tokens: Iterable[TPrimitive | None]) -> Self:
        """
        Combine the specified tokens with the current chain and return a new context instance.
        To make it easier to implement conditionally adding a token, the argument can be None
        to indicate that the current chain should not be modified.
        """

        # Get trial chain from the current context
        previous_chain = context.trial_chain if (context := active_or_none(cls)) is not None else None

        # Convert iterable to sequence, skipping None and checking each token for validity
        tokens = tuple(cls._checked_token(token) for token in tokens if token is not None)

        if not tokens:
            # If no tokens are provided, return the current context without modification
            return TrialContext(trial_chain=previous_chain).build()
        else:
            # Serialize and append the tokens to the previous chain
            serialized_tokens = [PrimitiveSerializers.DEFAULT.serialize(token) for token in tokens]
            if previous_chain:
                # Combine the previous chain and the new identifier
                return TrialContext(trial_chain=tuple([x for x in previous_chain] + serialized_tokens)).build()
            else:
                # Previous chain is empty, use serialized tokens as the entire chain
                return TrialContext(trial_chain=tuple(serialized_tokens)).build()

    @classmethod
    def get_trial(cls) -> str | None:
        """Concatenates trial identifiers from the context stack, returns None if no current context or all are None."""
        if (context := active_or_none(cls)) is not None and context.trial_chain:
            # Concatenate trial chain tokens from the current context if not None or empty
            return "\\".join(context.trial_chain)
        else:
            # Otherwise return None
            return None

    @classmethod
    def _checked_token(cls, token: TPrimitive) -> None:
        """Return an error if the token is not a primitive type."""
        if not is_primitive(token):
            # If the token is not a primitive type, raise an error
            primitive_class_names = ", ".join(PRIMITIVE_CLASS_NAMES)
            raise RuntimeError(
                f"A TrialContext must be one of the following primitive classes:\n"
                f"{primitive_class_names}\n"
                f"The following token of type {TypeUtil.name(token)} is not supported:\n"
                f"{ErrorUtil.wrap(token)}"
            )
        elif isinstance(token, str):
            if token == "":
                raise RuntimeError("An empty string is not a valid token for a TrialContext.")
            elif "\n" in token:
                raise RuntimeError("A token for a TrialContext cannot contain a newline character.")
            elif "\\" in token:
                raise RuntimeError(
                    "A token for a TrialContext cannot contain a backslash character because\n"
                    "it serves as token separator in trial identifier."
                )
            else:
                return token
        else:
            return token
