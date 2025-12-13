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
from typing import List
from typing import Self
from cl.runtime.contexts.context_manager import _STACK_DICT_VAR
from cl.runtime.contexts.context_manager import get_active_contexts_and_ids
from cl.runtime.contexts.context_manager import make_active_and_return_stack
from cl.runtime.contexts.context_manager import make_inactive
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.serializers.data_serializers import DataSerializers

_CONTEXT_SERIALIZER = DataSerializers.FOR_JSON
"""Serializer used to serialize and deserialize contexts to dicts, primitive types are passed through."""


@dataclass(slots=True, kw_only=True)
class ContextSnapshot(DataMixin):
    """
    When its 'capture_active' method is invoked, an instance of ContextSnapshot stores the active contexts for
    each (context_key_type, context_id) pair. The instance data can be serialized in JSON format for transfer
    to out-of-process task workers. It also acts as a context manager that saves the active contexts
    in the asynchronous environment it was called in and restores the active contexts it saves on __enter__,
    and reverses these steps on __exit__.
    """

    contexts: tuple[DataMixin, ...] = required()
    """Sequence of contexts for each unique (context_key_type, context_id) pair."""

    context_ids: tuple[str | None, ...] = required()
    """The value of context identifier for the corresponding context."""

    _processed_contexts: list[RecordProtocol] | None = None
    """
    Contexts for which __enter__ method has been called inside ContextSnapshot.__enter__ so far.
    For each of these contexts, __exit__ will be invoked in case of an exception.
    """

    _processed_context_stacks: list[list[RecordProtocol]] | None = None
    """Context stacks for which __enter__ method has been called inside ContextSnapshot.__enter__ so far."""

    _token: Token | None = None
    """Stores the state of all context stacks saved in __enter__ and restored in __exit__ of this class."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        if self.contexts is None:
            # Create an empty tuple if not initialized
            self.contexts = tuple()

        if self.context_ids is None:
            # Create a tuple filled with None of the same size as contexts if not initialized
            self.context_ids = (None,) * len(self.contexts)

        # Ensure the same length
        if (num_context_ids := len(self.context_ids)) != (num_contexts := len(self.contexts)):
            raise RuntimeError(
                f"The number of contexts {num_contexts} in ContextSnapshot does not match\n"
                f"the number of context identifiers {num_context_ids} "
            )

    def __enter__(self) -> Self:
        """Backup _STACK_DICT_VAR and invoke __enter__ for each item in 'contexts'."""

        # Checks to ensure previous __exit__ was completed successfully
        self.check_frozen()
        if self._token is None and self._processed_contexts is None and self._processed_context_stacks is None:
            # Backup the previous state of _STACK_DICT_VAR
            self._token = _STACK_DICT_VAR.set(None)
            # Initialize instance variables
            self._processed_contexts = []
            self._processed_context_stacks = []
        else:
            raise RuntimeError(
                "Attempting to run __enter__ on a ContextSnapshot instance where __exit__\n"
                "did not complete or raised an exception."
            )

        # Enter into each context in the order specified
        if self.contexts:
            for context, context_id in zip(self.contexts, self.context_ids):
                try:
                    # Activate context directly bypassing 'with' clause
                    context_stack = make_active_and_return_stack(context, context_id)
                    self._processed_contexts.append(context)
                    self._processed_context_stacks.append(context_stack)
                except Exception as exc:
                    # Deactivate in reverse order all of the previously activated contexts
                    # but not the context that raised an error in its __enter__ method
                    # since __exit__ should be invoked only if __enter__ completed successfully
                    while self._processed_contexts:
                        make_inactive(
                            self._processed_contexts.pop(),
                            exc_type=type(exc),
                            exc_val=exc,
                            exc_tb=exc.__traceback__,
                            expected_stack=self._processed_context_stacks.pop(),
                        )
                    # Exit from those contexts that were already processed before an exception occurred
                    # This is required because __exit__ is not called automatically when __enter__ raises an exception
                    self.__exit__(
                        exc_type=type(exc),
                        exc_val=exc,
                        exc_tb=exc.__traceback__,
                    )
                    # Rethrow
                    raise exc
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Invoke __exit__ for each item in 'contexts', restore _STACK_DICT_VAR, clear instance variables"""

        self.check_frozen()
        try:
            while self._processed_contexts:
                # Make inactive in reverse order all processed contexts
                make_inactive(
                    self._processed_contexts.pop(),
                    exc_type=exc_type,
                    exc_val=exc_val,
                    exc_tb=exc_tb,
                    expected_stack=self._processed_context_stacks.pop(),
                )
        finally:
            # Restore _STACK_DICT_VAR and clear instance variables
            if (
                self._token is not None
                and self._processed_contexts is not None
                and len(self._processed_contexts) == 0
                and self._processed_context_stacks is not None
                and len(self._processed_context_stacks) == 0
            ):
                _STACK_DICT_VAR.reset(self._token)
                self._token = None
                self._processed_contexts = None
                self._processed_context_stacks = None
            else:
                raise RuntimeError(
                    "Attempting to run __exit__ on a ContextSnapshot instance where __enter__\n"
                    "did not complete or raised an exception."
                )

    def to_json(self) -> str:
        """Serialize to JSON."""
        self.check_frozen()
        result = _CONTEXT_SERIALIZER.serialize(self)
        return result

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Deserialize from JSON."""
        result = _CONTEXT_SERIALIZER.deserialize(json_str)
        return result

    @classmethod
    def capture_active(cls) -> Self:
        """Capture active contexts from the current asynchronous environment."""
        contexts, context_ids = get_active_contexts_and_ids()
        result = ContextSnapshot(contexts=contexts, context_ids=context_ids).build()
        return result
