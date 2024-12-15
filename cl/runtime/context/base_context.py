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

import threading
from abc import ABC
from contextvars import ContextVar
from contextvars import Token
from dataclasses import dataclass
from dataclasses import field
from typing import List
from typing import Type
from typing import TypeVar
from typing_extensions import Self
from cl.runtime.context.context_extension import ContextExtension
from cl.runtime.records.dataclass_freezable import DataclassFreezable
from cl.runtime.records.record_util import RecordUtil

_CONTEXT_STACK_VAR: ContextVar[List | None] = ContextVar("_CONTEXT_STACK_VAR", default=None)
"""
Context adds self to the stack on __enter__ and removes self on __exit__.
Each asynchronous environment has its own stack.
"""

_DEFAULT_CONTEXT = None
"""Default context is created based on settings, then used to set values not modified explicitly by __init__ params."""

_DEFAULT_CONTEXT_LOCK = threading.Lock()
"""Thread lock for the default context."""

TContextExtension = TypeVar("TContextExtension")
"""Generic parameter for the context extension variable."""


@dataclass(slots=True, kw_only=True)
class BaseContext(DataclassFreezable, ABC):
    """Base class for Context, should not be initialized directly."""

    is_root: bool = False
    """Set this field to True when the context is used in the outermost 'with' clause."""

    is_deserialized: bool = False
    """Use this flag to determine if this context instance has been deserialized, e.g. inside an out-of-process task."""

    extensions: List[ContextExtension] | None = None
    """
    Context extensions provide additional functionality that is not built into the Context class.
    
    Notes:
        - Return the extension type specified in the constructor of the current context if specified
        - Otherwise search for the extension of the same type in the context chain
        - If no extension is found in the context chain for a given extension type, the default extension
          created from settings will be returned
        - Each extension type must be final and derived directly from ContextExtension base
    """

    def init(self) -> Self:
        """Initialize fields that are not set with values from the current context."""

        # Do not execute this code on frozen or deserialized context instances
        #   - If the instance is frozen, init_all has already been executed
        #   - If the instance is deserialized, init_all has been executed before serialization
        if not self.is_frozen() and not self.is_deserialized:

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
                        f"To run {class_name}.init_all() outside of 'with', use {class_name}(is_root=True, ...)\n"
                        f"If this error occurs inside a 'with' clause, this indicates the 'with' clause has been\n"
                        f"invoked in a different asynchronous environment (i.e., in a different thread or before\n"
                        f"entering an async function) than the current call to {class_name}.init_all().\n"
                    )

            if parent_context:
                # The fields variable will contain public fields for the final class and its bases
                # Exclude the extensions field which will be merged rather than replaced
                fields = [
                    field
                    for field in self.__dataclass_fields__.keys()
                    if not field.startswith("_") and not field == "extensions"
                ]
                # Set empty fields to the values from the current context if it is set, except for extensions
                for field in fields:
                    if getattr(self, field, None) is None:
                        if (current_value := getattr(parent_context, field, None)) is not None:
                            setattr(self, field, current_value)

            # Combine extensions with the parent type preserving order from base to derived,
            # except for the extensions that are present in the current context are omitted
            # from the parent contexts
            if self.extensions:
                # Check for duplicate extension types in the current context
                extension_types = [type(e) for e in self.extensions]
                ContextExtension.check_duplicate_types(extension_types, "extensions in the current context")
                # Initialize extensions in the current context
                [RecordUtil.init_all(x) for x in self.extensions]
            if parent_context and parent_context.extensions:
                # Check for duplicate extension types in the parent context
                parent_extension_types = [type(e) for e in parent_context.extensions]
                ContextExtension.check_duplicate_types(parent_extension_types, "extensions in the parent context")
                # Combine with parent
                if self.extensions:
                    # Both are present, combine preserving order from base to derived
                    # except base extensions that are present in derived are omitted
                    self.extensions = [
                        x for x in parent_context.extensions if type(x) not in extension_types
                    ] + self.extensions
                else:
                    # Only parent extensions are present, deep copy
                    self.extensions = list(parent_context.extensions)

        # Return self to enable method chaining
        return self

    @classmethod
    def reset_before(cls) -> Token:
        """Set context stack to None before async method execution, return a token for its previous state."""
        return _CONTEXT_STACK_VAR.set(None)

    @classmethod
    def reset_after(cls, token: Token) -> None:
        """Restore context stack to the previous state after async method execution."""
        _CONTEXT_STACK_VAR.reset(token)

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
                f"    before entering an async function) than the {cls.__name__}.current() method.\n"
            )

    def extension(self, extension_type: Type[TContextExtension]) -> TContextExtension:
        """Return the Extension instance of the specified type, error message if not found."""
        # Find the first context extension of the specified type (only one should be present, None if not found)
        result = next((x for x in self.extensions if isinstance(x, extension_type)), None) if self.extensions else None
        if result is None:
            # Return the default extension for this type if not found in self.extensions
            result = extension_type._default()  # noqa
        return result

    def __enter__(self):
        """Supports 'with' operator for resource disposal."""

        # Initialize to populate empty values from the current context or settings
        RecordUtil.init_all(self)

        # Freeze self and extensions to prevent further modifications (ok to call even if already frozen)
        self.freeze()
        if self.extensions:
            [x.freeze() for x in self.extensions]

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
                        f"entering an async function) than this clause.\n"
                    )

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
                f"than the environment where the exit from this clause had occurred.\n"
            )

        # Restore the previous current context on exiting from 'with Context(...)' clause
        current_context = context_stack.pop()
        if current_context is not self:
            class_name = {type(self).__name__}
            raise RuntimeError(
                f"Current context has been modified other than by entering into a\n"
                f"'with {class_name}(...)' clause in the same asynchronous\n"
                f"environment (i.e., the same thread and async function) as\n"
                f"the environment where the exit from this clause had occurred.\n"
            )

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
