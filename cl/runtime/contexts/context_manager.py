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

from collections import defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from typing import DefaultDict, Any
from typing import List
from typing import Optional
from typing import Type
from cl.runtime.records.cast_util import CastUtil
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.type_util import TypeUtil

_STACK_DICT_VAR: ContextVar[Optional[defaultdict[type, list[RecordProtocol]]]] = ContextVar(
    "_STACK_DICT_VAR",
    default=None,
)
"""
The argument of activate(...) is added to the stack on __enter__ and removed on __exit__ using its key type as dict key.
Each asynchronous environment has its own stack dictionary.
"""


def _get_or_create_stack_dict() -> DefaultDict[Type, List[RecordProtocol]]:
    """Get or create stack dictionary for the current asynchronous environment."""
    stack_dict = _STACK_DICT_VAR.get()
    if stack_dict is None:
        stack_dict = defaultdict(list)
        _STACK_DICT_VAR.set(stack_dict)
    return stack_dict


def _get_or_create_stack_dict() -> DefaultDict[Type, List[RecordProtocol]]:
    """Get or create stack dictionary for the current asynchronous environment."""
    stack_dict = _STACK_DICT_VAR.get()
    if stack_dict is None:
        stack_dict = defaultdict(list)
        _STACK_DICT_VAR.set(stack_dict)
    return stack_dict


def _get_or_create_stack(context_type: Type[RecordProtocol]) -> List[RecordProtocol]:
    """Get or create stack for the key type of the context in the current asynchronous environment."""
    key_type = context_type.get_base_type()
    return _get_or_create_stack_dict()[key_type]


def _activate_and_return_stack(context: TRecord) -> List[RecordProtocol]:
    """Helper method for activate(...), do not use directly except for context stack replication in ContextSnapshot."""

    # Invoke context.__enter__ method before making the context active if it is implemented
    # If this method raises an exception, the context will not be activated
    # and the exception will be propagated outside the 'with' clause
    if hasattr(context, "__enter__"):
        context.__enter__()

    # Check that the context is frozen, error otherwise
    context.check_frozen()

    # Get context stack for the __enter__ method in the current asynchronous environment
    enter_stack = _get_or_create_stack(type(context))

    # Activate the argument context by appending it to the context stack
    enter_stack.append(context)

    return enter_stack


def _deactivate_and_check_stack(
        context: TRecord,
        enter_stack: List[RecordProtocol],
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
) -> None:
    """
    Helper method for activate(...), do not use directly except for context stack replication in ContextSnapshot.

    Args:
        context: The context being deactivated.
        enter_stack: The stack used to activate the context (used to check it is the same instance)
        exc_type: Exception type (None if no exception)
        exc_val: Exception instance (None if no exception)
        exc_tb: The traceback object containing call stack information (None if no exception)
    """

    # Get context stack for the __exit__ method in the current asynchronous environment
    exit_stack = _get_or_create_stack(type(context))

    # Validate stack integrity and restore previous current
    if not exit_stack:
        raise RuntimeError(
            f"Context stack for {TypeUtil.name(context)} has been cleared inside 'with activate(...)' clause."
        )
    elif exit_stack is not enter_stack:
        raise RuntimeError(
            f"Context stack for {TypeUtil.name(context)} has been changed inside 'with activate(...)' clause."
        )

    # Deactivate the currently active context by removing it from the context stack
    deactivated = exit_stack.pop()
    if deactivated is not context:
        # Error message if it is not the same context as the argument
        raise RuntimeError(
            f"Active context of type {TypeUtil.name(context)} has been changed bypassing the context manager."
        )

    # After making the context inactive, invoke context.__exit__ method if it is implemented
    # Pass exception details if the code inside 'with activate(...)' clause raised an exception
    if hasattr(context, "__exit__"):
        context.__exit__(exc_type, exc_val, exc_tb)


@contextmanager
def activate(context: TRecord):
    """
    Set active context using 'with activate(context)' clause, context may or may not implement __enter__ and __exit__

    Notes:
        - If implemented __enter__, will be called before activation and __exit__ after deactivation
        - If an exception is raised inside 'with activate(context)' clause, its details will be passed to __exit__
    """

    # Add to the context stack for the context key type in the current asynchronous environment
    enter_stack = _activate_and_return_stack(context)

    try:
        # Pass control to the code inside 'with activate(context)' clause
        yield context
    except Exception as exc:
        # If the code inside 'with activate(context)' raises an exception, remove context from the stack
        # and pass exception details to context.__exit__ if it is implemented
        _deactivate_and_check_stack(context, enter_stack, type(exc), exc, exc.__traceback__)
        # Rethrow
        raise exc
    else:
        # Remove context from the stack
        _deactivate_and_check_stack(context, enter_stack, None, None, None)


def active(context_type: type[TRecord]) -> TRecord:
    """
    Return the argument of the innermost `with activate(...)` clause for the key type of context_type,
    or raise an error outside such 'with' clause.
    """
    stack = _get_or_create_stack(context_type)
    if stack:
        return CastUtil.cast(context_type, stack[-1])
    else:
        raise RuntimeError(
            f"The function active({TypeUtil.name(context_type)}) is invoked outside 'with activate(...)'\n"
            f"clause for the corresponding key type {TypeUtil.name(context_type.get_base_type())}.\n"
            f"Use active_or_none(...) to receive None instead of an exception."
        )


def active_or_none(context_type: type[TRecord]) -> TRecord | None:
    """
    Return the argument of the innermost `with activate(...)` clause for the key type of context_type,
    or None outside such 'with' clause.
    """
    stack = _get_or_create_stack(context_type)
    return CastUtil.cast(context_type, stack[-1]) if stack else None


def active_contexts() -> tuple[RecordProtocol, ...]:
    """
    Return a tuple of active contexts across all key types, or an empty tuple if none exist.
    This method is used by the ContextSnapshot to restore the active contexts for out-of-process
    task execution.
    """
    stack_dict = _STACK_DICT_VAR.get()
    if stack_dict is not None:
        # Each active contexts is last in its context stack, skip those that are None or empty
        return tuple(context_stack[-1] for context_stack in stack_dict.values() if context_stack)
    else:
        # Otherwise return an empty tuple
        return tuple()
