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

import random
import time

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from cl.runtime.context.context import Context
from cl.runtime.context.testing_context import TestingContext
        

# Create a local random instance with the seed
_RANDOM = random.Random(0)

def _sleep():
    """Sleep for a random interval from 0 to 1 sec."""
    duration = _RANDOM.uniform(0, 1)
    time.sleep(duration)

async def _sleep_async():
    """Sleep for a random interval from 0 to 1 sec."""
    duration = _RANDOM.uniform(0, 1)
    await asyncio.sleep(duration)

def _perform_testing():
    """Use for testing in-process or in multiple threads."""

    # Check that calling Context.current() here raises if called before entering 'with'
    with pytest.raises(RuntimeError):
        Context.current()

    with TestingContext() as current_context_1:

        # Sleep between entering 'with' clause and calling 'current'
        _sleep()

        # Check that current context is set inside 'with Context(...)' clause
        assert Context.current() is current_context_1

        # Sleep between entering 'with' clause and calling 'current'
        _sleep()

        # Check that creating a context object but not using it in 'with Context()'
        # clause does not change the current context
        other_context = Context()
        assert Context.current() is not other_context
        assert Context.current() is current_context_1

        with Context() as current_context_2:
            # Sleep between entering 'with' clause and calling 'current'
            _sleep()
            # New current context
            assert Context.current() is current_context_2

        # Sleep between entering 'with' clause and calling 'current'
        _sleep()

        # After exiting the second 'with' clause, the previous current context is restored
        assert Context.current() is current_context_1

    with pytest.raises(RuntimeError):
        # Sleep between entering 'with' clause and calling 'current'
        _sleep()
        # Check that calling Context.current() here raises if called after exiting 'with'
        Context.current()

async def _perform_testing_async():
    """Use for testing in async loop."""

    # Check that calling Context.current() here raises if called before entering 'with'
    with pytest.raises(RuntimeError):
        Context.current()

    with TestingContext() as current_context_1:

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async()

        # Check that current context is set inside 'with Context(...)' clause
        assert Context.current() is current_context_1

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async()

        # Check that creating a context object but not using it in 'with Context()'
        # clause does not change the current context
        other_context = Context()
        assert Context.current() is not other_context
        assert Context.current() is current_context_1

        with Context() as current_context_2:
            # Sleep between entering 'with' clause and calling 'current'
            await _sleep_async()
            # New current context
            assert Context.current() is current_context_2

        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async()

        # After exiting the second 'with' clause, the previous current context is restored
        assert Context.current() is current_context_1

    with pytest.raises(RuntimeError):
        # Sleep between entering 'with' clause and calling 'current'
        await _sleep_async()
        # Check that calling Context.current() here raises if called after exiting 'with'
        Context.current()

async def _gather():
    """Gather async functions."""
    await asyncio.gather(
        _perform_testing_async(),
        _perform_testing_async(),
        _perform_testing_async(),
        _perform_testing_async(),
        _perform_testing_async()
    )

def test_in_process():
    """Test in different threads."""

    # Perform testing in process
    _perform_testing()

def test_in_threads():
    """Test in different threads."""
    thread_count = 5
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(_perform_testing) for _ in range(thread_count)]
    for future in futures:
        future.result()

def test_in_async_loop():
    """Test in different async environments."""
    asyncio.run(_gather())


if __name__ == "__main__":
    pytest.main([__file__])
