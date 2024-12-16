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
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from random import Random
from cl.runtime.context.context import Context
from cl.runtime.context.testing_context import TestingContext
from stubs.cl.runtime.context.stub_base_extension_context import StubBaseExtensionContext
from stubs.cl.runtime.context.stub_derived_extension_context import StubDerivedExtensionContext

TASK_COUNT = 3
MAX_SLEEP_DURATION = 0.2


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
    rnd: Random,
    max_sleep_duration: float = MAX_SLEEP_DURATION,
):
    """Use for testing in-process or in multiple threads."""

    # Sleep before entering the task
    _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
    with TestingContext():

        _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        with pytest.raises(RuntimeError):
            # Ensure that current context is not leaked outside the 'with clause' before the test
            StubBaseExtensionContext.current()

        stub_context_1 = StubBaseExtensionContext(base_field="stub_context_1")
        with stub_context_1:

            _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
            assert StubBaseExtensionContext.current() is stub_context_1

            stub_context_2 = StubDerivedExtensionContext(derived_field="stub_context_2")
            with stub_context_2:
                _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
                assert StubDerivedExtensionContext.current() is stub_context_2

            assert StubBaseExtensionContext.current() is stub_context_1

        with pytest.raises(RuntimeError):
            # Ensure that current context is not leaked outside the 'with clause' after the test
            StubBaseExtensionContext.current()

async def _perform_testing_async(
    *,
    task_index: int,
    rnd: Random,
    is_inner: bool = False,
    max_sleep_duration: float = MAX_SLEEP_DURATION,
):
    """Use for testing in async loop."""

    # Sleep before entering the task
    await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
    with Context():

        await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

        with pytest.raises(RuntimeError):
            # Ensure that current context is not leaked outside the 'with clause' before the test
            StubBaseExtensionContext.current()

        stub_context_1 = StubBaseExtensionContext(base_field="stub_context_1")
        with stub_context_1:

            await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
            assert StubBaseExtensionContext.current() is stub_context_1

            stub_context_2 = StubDerivedExtensionContext(derived_field="stub_context_2")
            with stub_context_2:
                await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
                assert StubDerivedExtensionContext.current() is stub_context_2

            assert StubBaseExtensionContext.current() is stub_context_1

        with pytest.raises(RuntimeError):
            # Ensure that current context is not leaked outside the 'with clause' before the test
            StubBaseExtensionContext.current()


async def _gather(rnd: Random):
    """Gather async functions."""
    state_before = Context.reset_before()
    try:
        tasks = [_perform_testing_async(task_index=i, rnd=rnd) for i in range(TASK_COUNT)]
        await asyncio.gather(*tasks)
    finally:
        Context.reset_after(state_before)


def test_error_handling():
    """Test error handling in specifying extensions."""
    stub_context_1 = StubBaseExtensionContext(base_field="stub_context_1")
    stub_context_2 = StubDerivedExtensionContext(base_field="stub_context_2")

    # Outer context all of the fields of the inner context, ok
    with stub_context_1:
        with stub_context_2:
            pass

    # Outer context is missing some fields from the inner context, raise
    with pytest.raises(RuntimeError):
        with stub_context_2:
            with stub_context_1:
                pass


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
