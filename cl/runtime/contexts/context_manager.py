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
from typing import Any
from typing import Optional
from typing import Type
from cl.runtime.records.protocols import RecordProtocol
from cl.runtime.records.protocols import TRecord
from cl.runtime.records.typename import typename

_STACK_DICT_VAR: ContextVar[Optional[defaultdict[tuple[type, str | None], list[RecordProtocol]]]] = ContextVar(
    "_STACK_DICT_VAR",
    default=None,
)
"""
The argument of activate(...) is added to the stack on __enter__ and removed on __exit__ using its key type as dict key.
Each asynchronous environment has its own stack dictionary.
"""


def _get_or_create_stack_dict() -> defaultdict[tuple[type, str | None], list[RecordProtocol]]:
    """Get or create stack dictionary for the current asynchronous environment indexed by context key."""
    stack_dict = _STACK_DICT_VAR.get()
    if stack_dict is None:
        stack_dict = defaultdict(list)
        _STACK_DICT_VAR.set(stack_dict)
    return stack_dict


def _get_or_create_stack(context_type: Type[RecordProtocol], context_id: str | None = None) -> list[RecordProtocol]:
    """
    Get or create stack for the (context_key_type, context_id) pair in the current asynchronous environment.

    Args:
        context_type: Type of the context, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """
    if context_id == "":
        raise RuntimeError("Using an empty string as context_id is ambiguous, use None instead.")

    key_type_name = typename(context_type.get_key_type())
    return _get_or_create_stack_dict()[(key_type_name, context_id)]


def make_active_and_return_stack(context: TRecord, context_id: str | None = None) -> list[RecordProtocol]:
    """
    Similar to make_active(...) but returns context stack rather than the context.

    Args:
        context: Context object, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """

    # Check that the context is frozen, error otherwise
    context.check_frozen()

    # Invoke context.__enter__ method before making the context active if it is implemented
    # If this method raises an exception, the context will not be activated
    # and the exception will be propagated outside the 'with' clause
    if hasattr(context, "__enter__"):
        returned_context = context.__enter__()
        if returned_context is not None and returned_context is not context:
            raise RuntimeError("To use activate(context), context.__enter__() must return self or None.")

    # Get context stack for the __enter__ method in the current asynchronous environment
    context_stack = _get_or_create_stack(type(context), context_id)

    # Activate the argument context by appending it to the context stack
    context_stack.append(context)

    # Return for error checking purposes only
    return context_stack


def make_active(context: TRecord, context_id: str | None = None) -> TRecord:
    """
    Make context active without automatic deactivation, invokes context.__enter__ if it is implemented.

    Notes:
        - If the context is activated by make_active method, it must be explicitly deactivated by make_inactive method
        - Do not use this method for 'with' clause as it is will not automatically deactivate on 'with' clause exit,
          use 'with activate(...)' instead
        - This method invokes context.__enter__ method if present

    Args:
        context: Context object, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """

    # Add to the context stack for the (context_key_type, context_id) pair in the current asynchronous environment
    make_active_and_return_stack(context, context_id)
    return context


def make_inactive(
    context: TRecord,
    context_id: str | None = None,
    *,
    exc_type: Any = None,
    exc_val: Any = None,
    exc_tb: Any = None,
    expected_stack: list[RecordProtocol] | None = None,
) -> None:
    """
    Make context inactive and revert to the previous active context (if any).

    Notes:
        - This method must be called explicitly for contexts activated by make_active method
        - Do not use this method for contexts activated using 'with activate(...)' clause as they will be
          automatically deactivated on 'with' clause exit and do not require explicit deactivation
        - This method invokes context.__exit__ method if present

    Args:
        context: Context object, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
        exc_type: Exception type (None if no exception)
        exc_val: Exception instance (None if no exception)
        exc_tb: The traceback object containing call stack information (None if no exception)
        expected_stack: The stack that was used to activate the context for error checking only (not checked if None)
    """

    # Get context stack for the __exit__ method in the current asynchronous environment
    context_stack = _get_or_create_stack(type(context), context_id)

    # Validate stack integrity and restore previous current
    if not context_stack:
        raise RuntimeError(
            f"Context stack for context type {typename(context)} and context_id={context_id}\n"
            f"has been cleared inside 'with activate(...)' clause."
        )
    elif expected_stack and context_stack is not expected_stack:
        # Perform this check only if expected_stack is not None
        raise RuntimeError(
            f"Context stack for context type {typename(context)} and context_id={context_id}\n"
            f"has been changed inside 'with activate(...)' clause."
        )

    # Deactivate the currently active context by removing it from the context stack
    if context_stack[-1] is context:
        # Remove the top item in stack only if it is the same as context passed to this method
        context_stack.pop()
    else:
        raise RuntimeError(
            f"Active context for context type {typename(context)} and context_id={context_id}\n"
            f"has been changed bypassing the context manager."
        )

    # After making the context inactive, invoke context.__exit__ method if it is implemented
    # Pass exception details if the code inside 'with activate(...)' clause raised an exception
    if hasattr(context, "__exit__"):
        context.__exit__(exc_type, exc_val, exc_tb)


@contextmanager
def activate(context: TRecord, context_id: str | None = None):
    """
    Set active context using 'with activate(context)' clause, invokes __enter__ and __exit__ if they are implemented.
    If an exception is raised inside 'with activate(context)' clause, its details will be passed to __exit__.

    Args:
        context: Context object, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """

    # Add to the context stack for the context key type in the current asynchronous environment
    context_stack = make_active_and_return_stack(context, context_id)

    try:
        # Pass control to the code inside 'with activate(context)' clause, deactivate on return
        yield context
    except Exception as exc:
        # If the code inside 'with activate(context)' raises an exception, remove context from the stack
        # and pass exception details to context.__exit__ if it is implemented
        make_inactive(
            context,
            context_id,
            exc_type=type(exc),
            exc_val=exc,
            exc_tb=exc.__traceback__,
            expected_stack=context_stack,
        )
        # Rethrow
        raise exc
    else:
        # Remove context from the stack
        make_inactive(
            context,
            context_id,
            expected_stack=context_stack,
        )


@contextmanager
def activate_or_none(context: TRecord | None, context_id: str | None = None):
    """
    Set active context using 'with activate(context)' clause, invokes __enter__ and __exit__ if they are implemented.
    If an exception is raised inside 'with activate(context)' clause, its details will be passed to __exit__.

    Notes:
        Do nothing when context is None, this can be used for activating a context conditionally.

    Args:
        context: Context object, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """
    if context is not None:
        # Delegate to activate(...) when context is not None
        with activate(context, context_id) as activated_context:
            yield activated_context
    else:
        # Do nothing when context is None, this can be used for activating a context conditionally
        if context_id is not None:
            raise RuntimeError("If context is None, context_id must also be None.")
        yield None


def active(context_type: type[TRecord] | None, context_id: str | None = None) -> TRecord:
    """
    Return the argument of the innermost `with activate(...)` clause for the key type of context_type,
    or raise an error outside a 'with' clause for the corresponding (context_key_type, context_id) pair.

    Args:
        context_type: Type of the context, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """
    result = active_or_none(context_type, context_id)
    if result is not None:
        return result
    else:
        raise RuntimeError(
            f"Function active(context_type={typename(context_type)}, context_id={context_id}) invoked outside\n"
            f"'with activate(...) clause for the corresponding (context_key_type, context_id) pair.\n"
            f"Use active_or_none(...) to receive None instead of an exception."
        )


def active_or_none(context_type: type[TRecord], context_id: str | None = None) -> TRecord | None:
    """
    Return the argument of the innermost `with activate(...)` clause for the key type of context_type,
    or None outside a 'with' clause for the corresponding (context_key_type, context_id) pair.

    Args:
        context_type: Type of the context, active contexts are separate for each (context_key_type, context_id) pair.
        context_id: Optional context identifier for independent activation of multiple contexts of the same type.
    """
    stack = _get_or_create_stack(context_type, context_id)
    return stack[-1].cast(context_type) if stack else None


def active_or_default(context_type: type[TRecord]) -> TRecord:
    """
    Return the argument of the innermost `with activate(...)` clause for the key type of context_type,
    or create a default instance using 'context_type()' if outside a 'with' clause for the corresponding
    context_key_type.

    Notes:
        Context_id parameter not accepted for this method because default context is defined only for context_id == None

    Args:
        context_type: Type of the context, active contexts are separate for each (context_key_type, context_id) pair.
    """
    # Return the top context in stack if exists, otherwise build a new context instance with all values set to default
    # Context_id parameter not accepted for this method because default context is defined only for context_id == None
    result = active_or_none(context_type, context_id=None)
    if result is None:
        # Create a default instance if no active context is found for the (context_key_type, context_id) pair
        # The method 'default' is implemented in BuilderMixin to return cls().build(), derived types can override
        result = context_type.default()
    return result


def get_active_contexts_and_ids() -> tuple[tuple[RecordProtocol, ...], tuple[str | None, ...]]:
    """
    Return a tuple of (contexts, context_ids) for all active contexts, with empty tuples if no contexts are active.
    This method is used by the ContextSnapshot to restore the active contexts for out-of-process task execution.
    """
    stack_dict = _STACK_DICT_VAR.get()
    if stack_dict is not None:
        # Combine top context in each context stack with context_id or None, skip those that are None or empty
        context_and_id_pairs = tuple(
            (context_stack[-1], context_key[1]) for context_key, context_stack in stack_dict.items() if context_stack
        )
        if context_and_id_pairs:
            contexts, context_ids = zip(*context_and_id_pairs)
            return contexts, context_ids
        else:
            # Return an empty dict if there are no active contexts
            return (), ()
    else:
        # Return an empty dict if there are no active contexts
        return (), ()
