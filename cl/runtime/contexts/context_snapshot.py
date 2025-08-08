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

from contextvars import Token
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Sequence
from typing_extensions import Self
from cl.runtime.contexts.context_manager import _CONTEXT_STACK_DICT_VAR
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.serializers.data_serializers import DataSerializers

_CONTEXT_SERIALIZER = DataSerializers.FOR_JSON
"""Serializer used to serialize and deserialize contexts to dicts, primitive types are passed through."""


@dataclass(slots=True, kw_only=True)
class ContextSnapshot:
    """Records current context for each context key type and restores them during out-of-process task execution."""

    _all_contexts: List[RecordProtocol] | None = None
    """All contexts that will be entered into during out-of-process task execution."""

    _entered_contexts: List[RecordProtocol] | None = None
    """
    Contexts for which __enter__ method has been called inside ContextSnapshot.__enter__ so far.
    For each of these contexts, __exit__ will be invoked in case of an error in ContextSnapshot.__enter__ method.
    """

    _token: Token | None = None
    """Stores the state of all context stacks saved in __enter__ and restored in __exit__ of this class."""

    def __init__(self, data: Sequence[Dict]):
        """Create from contexts serialized into a list of dicts."""

        # Assign default values for each field to avoid not initialized errors
        self._all_contexts = None
        self._entered_contexts = None
        self._token = None

        # Deserialize and build if _all_contexts is not empty
        if data:
            self._all_contexts = _CONTEXT_SERIALIZER.deserialize(data)
            for context in self._all_contexts:
                # Build the deserialized record
                context.build()

    def __enter__(self) -> Self:
        """Invoke __enter__ for each item in the 'contexts' field."""

        # Set ContextVar=None before async task execution, get a token for restoring its previous state
        if self._token is None:
            self._token = self.save_and_clear_state()
        else:
            raise RuntimeError("Nested 'with' clauses are not permitted or necessary with ContextSnapshot.")

        # Ensure there are no stale entered contexts
        if self._entered_contexts:
            # Check if any exist
            raise RuntimeError("Stale context entry status detected in ContextSnapshot.")
        else:
            # Assign empty list as it could be None
            self._entered_contexts = []

        # Enter into each context in the order specified
        if self._all_contexts:
            for context in self._all_contexts:
                try:
                    context.__enter__()
                    self._entered_contexts.append(context)
                except Exception as e:
                    # This will call __exit__ in reverse order for all contexts entered into so far
                    # The exception is not passed to these __exit__ calls as it did not occur inside these contexts
                    self.__exit__(None, None, None)
                    # Rethrow
                    raise e
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Invoke __exit__ for each item in the 'contexts' field."""

        try:
            # Remove (pop) from the list and call __exit__ in reverse entry order on the contexts entered into so far
            while self._entered_contexts:
                # Remove the last remaining element
                entered_context = self._entered_contexts.pop()
                # Run __exit__ on the removed element with exception parameters
                entered_context.__exit__(exc_type, exc_val, exc_tb)
        finally:
            # Restore ContextVar to its previous state after async task execution using a token
            # from 'save_and_clear_state' whether or not an exception occurred
            if self._token is not None:
                self.restore_state(self._token)
            else:
                raise RuntimeError("Detected ContextSnapshot.__exit__ without a preceding ContextSnapshot.__enter__.")

    @classmethod
    def save_and_clear_state(cls) -> Token:
        """Save state for all context stacks into a token, then clear state."""
        return _CONTEXT_STACK_DICT_VAR.set(None)

    @classmethod
    def restore_state(cls, token: Token) -> None:
        """Restore state for all context stacks from the token returned by 'save_and_clear_state'."""
        _CONTEXT_STACK_DICT_VAR.reset(token)

    @classmethod
    def serialize_current_contexts(cls) -> Sequence[Dict]:
        """Serialize all current contexts to a list of dicts, each dict represents one serialized context."""

        # Get current contexts for all key types
        contexts = active_contexts()

        # Serialize
        result = cls._serialize_contexts(contexts)
        return result

    @classmethod
    def _serialize_contexts(cls, contexts: Sequence[RecordProtocol]) -> Sequence[Dict]:
        """Serialize argument contexts to a list of dicts, each dict represents one serialized context."""

        # Use serializer
        result = _CONTEXT_SERIALIZER.serialize(contexts)
        return result
