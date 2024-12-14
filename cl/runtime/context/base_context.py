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
from dataclasses import dataclass, field
from typing import List, Type, Dict

import asyncio
from typing_extensions import Self
from cl.runtime.records.dataclass_freezable import DataclassFreezable
from cl.runtime.records.record_util import RecordUtil

_CONTEXT_STACK_VAR: ContextVar[List[BaseContext] | None] = ContextVar("_CONTEXT_STACK_VAR", default=None)
"""
Context adds self to the stack on __enter__ and removes self on __exit__.
Each asynchronous environment has its own stack.
"""

_ROOT_CONTEXT_DICT: Dict[Type, BaseContext] = {}
"""Dictionary of root contexts by final type."""

_ROOT_CONTEXT_DICT_LOCK = threading.Lock()
"""Thread lock for the dictionary of root contexts by final type."""


@dataclass(slots=True, kw_only=True)
class BaseContext(DataclassFreezable, ABC):
    """Context extensions add features that are serialized with the context for out-of-process execution."""

    allow_root: bool = False
    """
    Creating the root context for the current asynchronous environment from settings 
    is permitted only when this field is True.
    
    Notes:
        - This field should be True only when there are no outer 'with' clauses, for example inside
          an async FastAPI route method or at the start of a unit test. 
        - In all other cases it should have the default value of False so the new context instance inherits
          its settings from the previous current context (i.e., the last context in stack for the current
          asynchronous environment).
        - Each asynchronous environment (the combination of thread and even loop within the thread)
          has its own context stack.
    """

    _is_root: bool = field(init=False, default=False)
    """Indicates that self is root context of the current asynchronous environment."""

    def init(self) -> Self:
        """Initialize fields that are not set with values from the current context."""
        
        # Inherit settings from the previous context in stack if present.
        # Each asynchronous environment has its own context stack.
        context_stack = _CONTEXT_STACK_VAR.get()
        current_context = context_stack[-1] if context_stack else None
        if current_context is not None:
            # The fields variable will contain public fields for the final class and its bases
            fields = [field for field in self.__dataclass_fields__.keys() if not field.startswith("_")]
            # Set empty fields to the values from the current context if it is set
            for field in fields:
                if getattr(self, field) is None:
                    if (current_value := getattr(current_context, field, None)) is not None:
                        setattr(self, field, current_value)
        elif self.allow_root:
            # Set flag indicating self is root context for the current asynchronous environment
            self._is_root = True
        else:
            class_name = type(self).__name__
            raise RuntimeError(f"Outside 'with {class_name}(...)' clause, a new {class_name} can only be created\n"
                               f"if allow_root=True is set. This flag permits creating the root context in the\n"
                               f"current asynchronous environment from settings.")

        # Return self to enable method chaining
        return self
    
    @classmethod
    def current(cls) -> Self:
        """Return the current context, or if does not exist create from settings if allow_root is True."""

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
            # Context stack not found, assign new root context only if allow_root=True
            if self.allow_root:
                context_stack = []
                _CONTEXT_STACK_VAR.set(context_stack)
            else:
                raise RuntimeError(
                    f"The outermost 'with' clause must use {type(self).__name__}(allow_root=True, ...) which\n"
                    f"will permit creating the root context for the current asynchronous environment from settings.")

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
