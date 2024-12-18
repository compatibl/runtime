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
from typing import List, Dict
from cl.runtime.context.base_context import BaseContext
from cl.runtime.serialization.dict_serializer import DictSerializer

_DICT_SERIALIZER = DictSerializer()
"""Serializer used to serialize and deserialize contexts."""

@dataclass(slots=True, kw_only=True)
class ContextManager:
    """Records current context for each context key type and restores them during out-of-process task execution."""

    _all_contexts: List[BaseContext] | None = None
    """All contexts that will be entered into during out-of-process task execution."""

    _entered_contexts: List[BaseContext] | None = None
    """The current list of entered contexts."""

    _token: Token | None = None
    """Context token is saved in ContextManager.__enter__ and restored in ContextManager.__exit__."""

    def __init__(self, data: List[Dict]):
        """Create from contexts serialized into a list of dicts."""

        # Assign default values for each field to avoid not initialized errors
        self._all_contexts = None
        self._entered_contexts = None
        self._token = None

        # Deserialize if data is not empty
        if data:
            self._all_contexts = _DICT_SERIALIZER.deserialize_data(data, list)

        # Perform checks and apply settings
        if self._all_contexts:
            for context in self._all_contexts:

                # Ensure context is derived from BaseContext
                if not isinstance(context, BaseContext):
                    raise RuntimeError(f"Context {type(context).__name__} cannot be activated by ContextManager "
                                       f"because it is not derived from {BaseContext.__name__}.")

                # Mark as deserialized to prevent repeat initialization
                context.is_deserialized = True

    def __enter__(self):
        """Invoke __enter__ for each item in the 'contexts' field."""

        # Save contextvars before entering into contexts
        if self._token is None:
            self._token = BaseContext.reset_before()
        else:
            raise RuntimeError("Nested 'with' clauses are not permitted or necessary with ContextManager.")

        # Ensure there are no stale entered contexts
        if self._entered_contexts:
            # Check if any exist
            raise RuntimeError("Stale context entry status detected in ContextManager.")
        else:
            # Assign empty list as it could be None
            self._entered_contexts = []

        # Enter into each context in the order specified, skip if self._contexts is None or empty
        if self._all_contexts:
            for context in self._all_contexts:
                try:
                    context.__enter__()
                    self._entered_contexts.append(context)
                except Exception as e:
                    # Call __exit__ in reverse entry order with exception details on the context entered into
                    # when the exception occurred and clear self._entered_contexts field
                    self._exit_and_clear_entered_contexts(e)

                    # Exit the for loop if an exception had occurred
                    break


    def __exit__(self, exc_type, exc_val, exc_tb):
        """Invoke __exit__ for each item in the 'contexts' field."""

        # Call __exit__ in reverse entry order on the contexts entered into so far
        # and clear self._entered_contexts field
        self._exit_and_clear_entered_contexts()

        # Only after exiting from all contexts can we restore contextvars
        if self._token is not None:
             BaseContext.reset_after(self._token)
        else:
            raise RuntimeError("Detected ContextManager.__exit__ without a preceding ContextManager.__enter__.")

        # Return False to propagate exception to the caller
        return False

    @classmethod
    def serialize_all_current(cls) -> List[Dict]:
        """Serialize all current contexts to a list of dicts, each dict represents one serialized context."""

        # Get current contexts for all key types
        contexts = BaseContext.all_current()

        # Serialize
        result = cls._serialize_contexts(contexts)
        return result

    @classmethod
    def _serialize_contexts(cls, contexts: List[BaseContext]) -> List[Dict]:
        """Serialize argument contexts to a list of dicts, each dict represents one serialized context."""

        # Use serializer
        result = _DICT_SERIALIZER.serialize_data(contexts)

        # Set is_deserialized to True to prevent repeated initialization
        if result:
            for context_data in result:
                context_data["is_deserialized"] = True
        return result

    def _exit_and_clear_entered_contexts(self, e: Exception | None = None) -> None:
        """Manually call __exit__ for the contexts entered into with exception details if provided."""
        exc_type = type(e) if e else None
        exc_value = e
        exc_traceback = e.__traceback__ if e else None
        while self._entered_contexts:
            # Remove the last remaining element
            entered_context = self._entered_contexts.pop()
            # Run __exit__ on the removed element with exception parameters
            entered_context.__exit__(exc_type, exc_value, exc_traceback)