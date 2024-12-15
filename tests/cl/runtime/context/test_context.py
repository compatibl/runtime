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

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from random import Random

from cl.runtime.context.context import Context
from cl.runtime.context.testing_context import TestingContext
from cl.runtime.context.base_context import _CONTEXT_STACK_VAR  # noqa

TASK_COUNT = 5
MAX_SLEEP_DURATION = 0.5

def _sleep(*, task_index: int, rnd: Random, max_sleep_duration: float):
    """Sleep for a random interval, reducing the interval for higher task index."""
    duration = rnd.uniform(0, max_sleep_duration) * (TASK_COUNT - task_index) / TASK_COUNT
    time.sleep(duration)

async def _sleep_async(*, task_index: int, rnd: Random, max_sleep_duration: float):
    """Sleep for a random interval, reducing the interval for higher task index."""
    duration = rnd.uniform(0, max_sleep_duration) * (TASK_COUNT - task_index) / TASK_COUNT
    await asyncio.sleep(duration)

def _perform_testing(
        *,
        task_index: int,
        rnd: Random, is_inner: bool = False,
        max_sleep_duration: float = MAX_SLEEP_DURATION,
):
    """Use for testing in-process or in multiple threads."""
    
    # Use a temporary TestingContext without custom contex_id to get db for the subsequent named contexts
    with TestingContext() as temp_context:
        db = temp_context.db

    # Task label
    task_label = f"async task {task_index}{'.inner' if is_inner else ''}"

    # Sleep before entering the task
    _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    # Check for the current context
    if is_inner:
        # Inside the inner task the current context is set by the outer task
        print(f"Verified {Context.current().context_id} before the {task_label}")
    else:
        # Otherwise it was leaked from the outside environment, raise an error if current context remains
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is not None and len(context_stack) > 0:
            context_id = context_stack[-1].context_id  # noqa
            raise RuntimeError(f"Leaked context from the outside asynchronous environment before the {task_label}:\n"
                               f"{context_id}")

    context_id_1 = f"Context A for {task_label}"
    with TestingContext(context_id=context_id_1, db=db) as context_a:
        print(f"Inside {task_label}: Enter Context A")

        # Sleep between entering 'with' clause and calling 'current'
        _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # Check that current context is set inside 'with Context(...)' clause
        assert Context.current() is context_a

        # Sleep between entering 'with' clause and calling 'current'
        _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # Check that creating a context object but not using it in 'with Context()'
        # clause does not change the current context
        other_context = Context()
        assert Context.current() is not other_context
        assert Context.current() is context_a

        context_id_2 = f"Context B for {task_label}"
        with Context(context_id=context_id_2, db=db) as context_b:
            print(f"Inside {task_label}: Enter Context B")

            # Sleep between entering 'with' clause and calling 'current'
            _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

            # Run an inner method that changes the context
            if not is_inner:
                _perform_testing(
                    task_index = task_index,
                    rnd=rnd,
                    is_inner=True,
                    max_sleep_duration=max_sleep_duration
                )

            # New current context
            assert Context.current() is context_b
            print(f"Inside {task_label}: Exit Context B")

        # Sleep between entering 'with' clause and calling 'current'
        _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # After exiting the second 'with' clause, the previous current context is restored
        assert Context.current() is context_a
        print(f"Inside {task_label}: Exit Context A")

    # Sleep between entering 'with' clause and calling 'current'
    _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    # Check for the current context
    if is_inner:
        # Inside the inner task the current context is set by the outer task
        print(f"Verified {Context.current().context_id} after the {task_label}")
    else:
        # Otherwise it was leaked from the outside environment, raise an error if current context remains
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is not None and len(context_stack) > 0:
            context_id = context_stack[-1].context_id  # noqa
            raise RuntimeError(f"Leaked context from the outside asynchronous environment after the {task_label}:\n"
                               f"{context_id}")

async def _perform_testing_async(
        *,
        task_index: int,
        rnd: Random, is_inner: bool = False,
        max_sleep_duration: float = MAX_SLEEP_DURATION,
):
    """Use for testing in async loop."""

    # Use a temporary TestingContext without custom contex_id to get db for the subsequent named contexts
    with TestingContext() as temp_context:
        db = temp_context.db
    
    # Task label
    task_label = f"async task {task_index}{'.inner' if is_inner else ''}"

    # Sleep before starting the test
    await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    # Check for the current context
    if is_inner:
        # Inside the inner task the current context is set by the outer task
        print(f"Verified {Context.current().context_id} before the {task_label}")
    else:
        # Otherwise it was leaked from the outside environment, raise an error if current context remains
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is not None and len(context_stack) > 0:
            context_id = context_stack[-1].context_id  # noqa
            raise RuntimeError(f"Leaked context from the outside asynchronous environment before the {task_label}:\n"
                               f"{context_id}")

    context_id_1 = f"Context A for {task_label}"
    with TestingContext(context_id=context_id_1, db=db) as context_a:
        print(f"Inside {task_label}: Enter Context A")

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # Check that current context is set inside 'with Context(...)' clause
        assert Context.current() is context_a

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # Check that creating a context object but not using it in 'with Context()'
        # clause does not change the current context
        other_context = Context()
        assert Context.current() is not other_context
        assert Context.current() is context_a

        context_id_2 = f"Context B for {task_label}"
        with Context(context_id=context_id_2, db=db) as context_b:
            print(f"Inside {task_label}: Enter Context B")

            # Sleep between entering 'with' clause and calling 'current'
            await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

            # Await an async method that changes the context
            if not is_inner:
                await _perform_testing_async(
                    task_index = task_index,
                    rnd=rnd,
                    is_inner=True,
                    max_sleep_duration=max_sleep_duration
                )

            # New current context
            assert Context.current() is context_b
            print(f"Inside {task_label}: Exit Context B")

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        # After exiting the second 'with' clause, the previous current context is restored
        assert Context.current() is context_a
        print(f"Inside {task_label}: Exit Context A")


    # Sleep between entering 'with' clause and calling 'current'
    await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    # Check for the current context
    if is_inner:
        # Inside the inner task the current context is set by the outer task
        print(f"Verified {Context.current().context_id} after the {task_label}")
    else:
        # Otherwise it was leaked from the outside environment, raise an error if current context remains
        context_stack = _CONTEXT_STACK_VAR.get()
        if context_stack is not None and len(context_stack) > 0:
            context_id = context_stack[-1].context_id  # noqa
            raise RuntimeError(f"Leaked context from the outside asynchronous environment after the {task_label}:\n"
                               f"{context_id}")

async def _gather(rnd: Random):
    """Gather async functions."""
    tasks = [_perform_testing_async(task_index=i, rnd=rnd) for i in range(TASK_COUNT)]
    await asyncio.gather(*tasks)

def test_in_process():
    """Test in different threads."""
    
    # Create a local random instance with seed
    rnd = Random(0)

    # Run sequentially in-process
    [_perform_testing(task_index=task_index, rnd=rnd, max_sleep_duration=0) for task_index in range(TASK_COUNT)]

def test_in_threads():
    """Test in different threads."""

    # Create a local random instance with seed
    rnd = Random(0)
    
    # Run in parallel threads
    with ThreadPoolExecutor(max_workers=TASK_COUNT) as executor:
        futures = [
            executor.submit(_perform_testing, **{"task_index": task_index, "rnd": rnd})
            for task_index in range(TASK_COUNT)
        ]
    for future in futures:
        future.result()

def test_in_async_loop():
    """Test in different async environments."""

    # Save previous state of context stack before async method execution
    state_before = Context.reset_before()
    try:
        # Create a local random instance with seed
        rnd = Random(0)

        # Run using cooperative multitasking (asyncio)
        asyncio.run(_gather(rnd))
    finally:
        # Restore previous state of context stack after async method execution even if an exception occurred
        Context.reset_after(state_before)


if __name__ == "__main__":
    pytest.main([__file__])
