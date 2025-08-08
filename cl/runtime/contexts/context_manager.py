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

from contextlib import contextmanager
from contextvars import ContextVar
from collections import defaultdict
from typing import Type, TypeVar, DefaultDict, List, Optional, cast

from cl.runtime.records.protocols import RecordProtocol, TRecord

# Dict: { class -> [instances stack] } kept per async context
_CONTEXT_STACK_DICT_VAR: ContextVar[Optional[defaultdict[type, list[RecordProtocol]]]] = ContextVar(
    "_CONTEXT_STACK_DICT_VAR", default=None
)

def _typename(obj_or_type) -> str:
    try:
        return obj_or_type.__name__ if isinstance(obj_or_type, type) else type(obj_or_type).__name__
    except Exception:
        return str(obj_or_type)

def _stacks_dict() -> DefaultDict[Type, List[object]]:
    stacks = _CONTEXT_STACK_DICT_VAR.get()
    if stacks is None:
        stacks = defaultdict(list)
        _CONTEXT_STACK_DICT_VAR.set(stacks)
    return stacks

def _stack_for(cls: Type) -> List[object]:
    key_type = cls.get_base_type()
    return _stacks_dict()[key_type]

@contextmanager
def activate(context: TRecord):
    """
    Push `instance` onto its class-specific context stack for the current async context,
    then pop it on exit. Validates that the stack isn't mutated from the inside.
    """
    context_type = type(context)

    # Optional parity with your mixin: enforce "frozen" contract if present
    if hasattr(context, "is_frozen") and callable(getattr(context, "is_frozen")):
        if not context.is_frozen():  # type: ignore[attr-defined]
            raise RuntimeError(
                f"Context instance of type {_typename(context)} must be frozen before "
                f"entering 'with' clause. Invoke 'build' or 'freeze' first."
            )

    stack = _stack_for(context_type)

    # Prevent double-activating the *same* instance at the top
    if stack and stack[-1] is context:
        raise RuntimeError(
            f"The {_typename(context)} instance activated using 'with' operator is already current."
        )

    stack.append(context)
    try:
        yield context
    finally:
        # Validate stack integrity and restore previous current
        cur_stack = _stack_for(context_type)
        if not cur_stack:
            raise RuntimeError(
                f"Current {_typename(context)} stack has been cleared inside "
                f"'with {_typename(context)}(...)' clause."
            )
        current = cur_stack.pop()
        if current is not context:
            raise RuntimeError(
                f"Current {_typename(context)} has been modified inside "
                f"'with {_typename(context)}(...)' clause."
            )

def active(cls: Type[TRecord]) -> TRecord:
    """
    Return the current (innermost) active instance for `cls`.
    Raises outside the outermost `with activate(...)` block.
    """
    stack = _stack_for(cls)
    if stack:
        return cast(TRecord, stack[-1])
    raise RuntimeError(
        f"{_typename(cls)} is undefined outside the outermost "
        f"'with activate({_typename(cls)}(...))' clause.\n"
        f"Use active_or_none({_typename(cls)}) if you prefer None."
    )

def active_or_none(cls: Type[TRecord]) -> Optional[TRecord]:
    """Optional helper: returns the current instance or None when none is active."""
    stack = _stack_for(cls)
    return cast(Optional[TRecord], stack[-1]) if stack else None

def active_contexts() -> List[RecordProtocol]:
    """
    Return the list of current contexts across all key types, or an empty list if none exist.
    This method is used by the ContextSnapshot to restore the current contexts for out-of-process
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