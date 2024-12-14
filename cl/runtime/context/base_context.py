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

from __future__ import annotations
import threading
from abc import ABC
from contextvars import ContextVar
from dataclasses import dataclass
from typing import List
from typing_extensions import Self
from cl.runtime.records.dataclass_freezable import DataclassFreezable
from cl.runtime.records.record_util import RecordUtil

_CONTEXT_STACK_VAR: ContextVar[List[BaseContext] | None] = ContextVar("_CONTEXT_STACK_VAR", default=None)
"""
Context adds self to the stack on __enter__ and removes self on __exit__.
Each asynchronous environment has its own stack.
"""

_DEFAULT_CONTEXT: BaseContext | None = None
"""Default context is created based on settings."""

_DEFAULT_CONTEXT_LOCK = threading.Lock()
"""Thread lock for the default context."""


@dataclass(slots=True, kw_only=True)
class BaseContext(DataclassFreezable, ABC):
    """Context extensions add features that are serialized with the context for out-of-process execution."""

    is_root: bool = False
    """True when the context is used in the outermost 'with' clause."""

    def init(self) -> Self:
        """Initialize fields that are not set with values from the current context."""
        
        # Inherit settings from the previous context in stack if present.
        # Each asynchronous environment has its own context stack.
        context_stack = _CONTEXT_STACK_VAR.get()
        parent_context = context_stack[-1] if context_stack else None
        if parent_context is None:
            if self.is_root:
                if _DEFAULT_CONTEXT is not None and self is not _DEFAULT_CONTEXT:
                    # Do not set from parent context when initializing the default context
                    parent_context = _DEFAULT_CONTEXT
            else:
                class_name = type(self).__name__
                raise RuntimeError(
                    f"To run {class_name}.init_all() outside of 'with' clause, use {class_name}(is_root=True, ...)\n"
                    f"If this error occurs inside a 'with' clause, this indicates the 'with' clause has been\n"
                    f"invoked in a different asynchronous environment (i.e., in a different thread or before\n"
                    f"entering an async function) than the current call to {class_name}.init_all().\n")

        if parent_context:
            # The fields variable will contain public fields for the final class and its bases
            fields = [field for field in self.__dataclass_fields__.keys() if not field.startswith("_")]
            # Set empty fields to the values from the current context if it is set
            for field in fields:
                if getattr(self, field) is None:
                    if (current_value := getattr(parent_context, field, None)) is not None:
                        setattr(self, field, current_value)

        # Return self to enable method chaining
        return self

    @classmethod
    def current(cls) -> Self:
        """Return the current context, or if does not exist create from settings if is_root is True."""

        # Get context stack for the current asynchronous environment
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack and len(context_stack) > 0:
            return context_stack[-1]
        else:
            raise RuntimeError(
                f"A 'with {cls.__name__}(...)' clause has either:\n"
                f"  - Not been invoked before calling the {cls.__name__}.current() method, or\n"
                f"  - Has been invoked in a different asynchronous environment (i.e., in a different thread or\n"
                f"    before entering an async function) than the {cls.__name__}.current() method.\n")

    def __enter__(self):
        """Supports 'with' operator for resource disposal."""

        # Initialize to populate empty values from the current context or settings
        RecordUtil.init_all(self)

        # Freeze to prevent further modifications (ok to call even if already frozen)
        self.freeze()

        # Get context stack for the current asynchronous environment
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is None:
            if context_stack is None:
                # Context stack not found, assign new root context only if allow_root=True
                if self.is_root:
                    context_stack = []
                    _CONTEXT_STACK_VAR.set(context_stack)
                else:
                    class_name = type(self).__name__
                    raise RuntimeError(
                        f"The outermost 'with' clause in each asynchronous environment (thread and async method)\n"
                        f"must set is_root flag to True: 'with {class_name}(is_root=True, ...)'\n"
                        f"If this error occurred inside a 'with' clause, this indicates it has been invoked\n"
                        f"in a different asynchronous environment (i.e., in a different thread or before\n"
                        f"entering an async function) than this clause.\n")

        # Check if self is already the current context
        if context_stack and context_stack[-1] is self:
            raise RuntimeError("The context activated using 'with' operator is already current.")

        # Set current context on entering 'with ContextType(...)' clause
        context_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Supports 'with' operator for resource disposal."""

        # Get context stack for the current asynchronous environment
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is None or len(context_stack) == 0:
            class_name = {type(self).__name__}
            raise RuntimeError(
                f"A 'with {class_name.__name__}(...)' clause has been invoked in a different asynchronous\n"
                f"environment (i.e., in a different thread or before entering an async function)\n"
                f"than the environment where the exit from this clause had occurred.\n")

        # Restore the previous current context on exiting from 'with Context(...)' clause
        current_context = context_stack.pop()
        if current_context is not self:
            class_name = {type(self).__name__}
            raise RuntimeError(
                f"Current context has been modified other than by entering into a\n"
                f"'with {class_name}(...)' clause in the same asynchronous\n"
                f"environment (i.e., the same thread and async function) as\n"
                f"the environment where the exit from this clause had occurred.\n")

        # Return False to propagate exception to the caller
        return False

    @classmethod
    def _default(cls) -> Self:
        """
        Return the default context, or create if it does not exist.

        Notes:
            The 'with' clause does not change the root context which is based solely on settings.
            To use the context set using 'with' clause, use the 'current' method instead.
        """

        # Check if default context already exists
        global _DEFAULT_CONTEXT
        if _DEFAULT_CONTEXT is None:
            created_context = cls(is_root=True)
            RecordUtil.init_all(created_context)
            with _DEFAULT_CONTEXT_LOCK:
                # If another thread created the root context it after the initial check above
                # but before the following line, the existing value will be returned.
                # Otherwise, the created value will be added to the dict and returned.
                _DEFAULT_CONTEXT = created_context
        return _DEFAULT_CONTEXT
