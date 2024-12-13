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

from contextvars import ContextVar
from dataclasses import dataclass
from typing import Dict, Type, Any, TypeVar

_STACK_DICT: ContextVar = ContextVar("_STACK_DICT", default=None)
"""
Each context extension adds self to the stack value where its type is key on __enter__ and removes self on __exit__.
Each asynchronous context has its own stack dictionary.
"""

_ASYNC_SENTINEL: ContextVar = ContextVar("_ASYNC_SENTINEL", default=False)
"""Helps detect if async context is not the process root."""

_ASYNC_SENTINEL.set(True)
"""Set to true in the process root async context where import is running."""

_CONTEXT_DICT: Dict[str, Any] = {}
"""Stores the current context for each prefix."""

TContext = TypeVar("TContext")

@dataclass(slots=True, kw_only=True)
class ContextManager:
    """Records current context for each context type to restore them during out-of-process task execution."""

    @classmethod
    def current(cls, context_type: Type[TContext]) -> TContext:
        """
        Return the current instance of context for the specified type or None if not set.
        This method will run in every async context.
        """
        return _CONTEXT_DICT.get(context_type, None)

    @classmethod
    def update(cls, context: Any) -> None:
        """
        The current context is stored separately for each context type.
        This method will raise an error if async context is not process root.
        """
        if not _ASYNC_SENTINEL:
            raise RuntimeError("Current context can only be updated in async context of the process root.")
        _CONTEXT_DICT[type(context)] = context

