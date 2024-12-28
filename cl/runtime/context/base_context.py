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

from abc import ABC, abstractmethod
from collections import defaultdict
from contextvars import ContextVar
from dataclasses import dataclass
from typing import DefaultDict
from typing import List
from typing_extensions import Self
from cl.runtime.records.record_util import RecordUtil

_CONTEXT_STACK_DICT_VAR: ContextVar[DefaultDict[str, List] | None] = ContextVar("_CONTEXT_STACK_DICT_VAR", default=None)
"""
Context adds self to the stack on __enter__ and removes self on __exit__,
Each asynchronous environment has its own stack dictionary
"""


@dataclass(slots=True, kw_only=True)
class BaseContext(ABC):
    """Abstract base of context classes."""

    is_deserialized: bool = False
    """Use this flag to determine if this context instance has been deserialized, e.g. inside an out-of-process task."""

    @classmethod
    @abstractmethod
    def get_context_type(cls) -> str:
        """
        The lookup of current context for cls will be done using the key returned by cls.get_context_type().

        Notes:
          - Contexts that have different key types are isolated from each other and have independent 'with' clauses.
          - By convention, the returned string is the name of the base class for this context type in PascalCase
        """

    def init(self) -> Self:
        """Initialize fields that are not set with values from the current context."""

        # If the instance is deserialized, init_all has been executed before serialization
        # TODO: Review and determine if init_all must be executed in celery
        if False and not self.is_deserialized:  # TODO: !!!!!!!!!!!!!!!!!!!!!!!

            # Each asynchronous environment has its own context stack.
            context_stack = self._get_context_stack()

            # Look for parent context in context stack, it will be empty outside the outermost 'with' clause
            parent_context = context_stack[-1] if context_stack else None

            # Copy fields from the parent context if they are not set in the current context
            if parent_context:

                # Raise if the new context is missing some fields present in the parent context
                # Get public fields for the final class and its bases of self and parent_context
                self_fields = [x for x in self.__dataclass_fields__.keys() if not x.startswith("_")]
                parent_fields = [x for x in parent_context.__dataclass_fields__.keys() if not x.startswith("_")]
                missing_fields = [x for x in parent_fields if x not in self_fields]
                if missing_fields:
                    missing_fields_str = "\n".join(missing_fields)
                    raise RuntimeError(
                        f"Creating a context with type {type(self).__name__} which is missing some of the fields\n"
                        f"present in the current context type {type(parent_context).__name__} is not permitted.\n"
                        f"Missing fields: {missing_fields_str}\n"
                    )

                # Set empty fields to the values from the parent context
                for field in parent_fields:
                    if getattr(self, field, None) is None:
                        if (current_value := getattr(parent_context, field, None)) is not None:
                            setattr(self, field, current_value)

        # Return self to enable method chaining
        return self

    @classmethod
    def current_or_none(cls) -> Self:
        """Return the context from the innermost 'with' for cls.key_type(), or None outside the outermost 'with'."""

        # Get context stack for the current asynchronous environment
        context_stack = cls._get_context_stack()

        # Return if current context exists, or None if it is empty
        if context_stack:
            return context_stack[-1]
        else:
            return None

    @classmethod
    def current(cls) -> Self:
        """Return the context from the innermost 'with' for cls.key_type(), error outside the outermost 'with'."""

        # Get current context stack or None if it is empty
        result = cls.current_or_none()

        # Return if exists, otherwise error message
        if result:
            return result
        else:
            raise RuntimeError(
                f"{cls.__name__}.current() is undefined outside the outermost 'with {cls.__name__}(...)' clause.\n"
                f"To receive None instead of an exception, use {cls.__name__}.current_or_none()\n"
            )

    @classmethod
    def all_current(cls) -> List[Self]:
        """
        Return the list of current contexts across all key types, or an empty list if none exist.
        This method is used by the ContextManager to restore the current contexts for out-of-process
        task execution.
        """
        context_stack_dict = _CONTEXT_STACK_DICT_VAR.get()
        if context_stack_dict is not None:
            # Get current contexts as last in each context stack, skip those that are None or empty
            result = [context_stack[-1] for context_stack in context_stack_dict.values() if context_stack]
        else:
            # Otherwise return an empty list
            result = []
        return result

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource disposal."""

        # Initialize to populate empty values from the current context or settings
        RecordUtil.init_all(self)

        # Get context stack for the current asynchronous environment, at least one element is guaranteed
        # because constructing_default parameter is not passed
        context_stack = self._get_context_stack()

        # Check if self is already the current context
        if context_stack and context_stack[-1] is self:
            class_name = {type(self).__name__}
            raise RuntimeError(f"The {class_name} instance activated using 'with' operator is already current.")

        # Set current context on entering 'with ContextType(...)' clause
        context_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Supports 'with' operator for resource disposal."""

        # Get context stack for the current asynchronous environment
        context_stack = self._get_context_stack()
        if context_stack is None or len(context_stack) == 0:
            class_name = type(self).__name__
            raise RuntimeError(f"Current {class_name} stack has been cleared inside 'with {class_name}(...)' clause.")

        # Restore the previous current context on exiting from 'with Context(...)' clause
        current_context = context_stack.pop()
        if current_context is not self:
            class_name = {type(self).__name__}
            raise RuntimeError(f"Current {class_name} has been modified inside 'with {class_name}(...)' clause.")

        # Return False to propagate the exception (if any) that occurred inside the 'with' block
        return False

    @classmethod
    def _get_context_stack(cls) -> List[Self]:
        """Return context stack for cls.get_context_type()."""

        # Get context stack dict, create if None
        context_stack_dict = _CONTEXT_STACK_DICT_VAR.get()
        if context_stack_dict is None:
            context_stack_dict = defaultdict(list)
            _CONTEXT_STACK_DICT_VAR.set(context_stack_dict)

        # Look up in dict using cls.get_context_type() rather than cls itself
        context_type = cls.get_context_type()

        # The defaultdict will create an empty list if the key does not exist
        context_stack = context_stack_dict[context_type]
        return context_stack
