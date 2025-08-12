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
from cl.runtime.contexts.context_manager import activate, activate_or_none
from cl.runtime.contexts.context_manager import active
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.contexts.context_manager import make_active, make_inactive
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from stubs.cl.runtime.contexts.stub_context import StubContext
from stubs.cl.runtime.contexts.stub_derived_context import StubDerivedContext

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

    # Ensure current context is not leaked outside 'with' clauses before the test
    assert active_or_none(StubContext) is None
    _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    with pytest.raises(RuntimeError):
        # Ensure that current context is not leaked outside the 'with clause' before the test
        active(StubContext)

    stub_context_1 = StubContext(id="stub_context_1").build()
    with activate(stub_context_1):

        _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
        assert active(StubContext) is stub_context_1

        stub_context_2 = StubDerivedContext(derived_field="stub_context_2").build()
        with activate(stub_context_2):
            _sleep(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
            assert active(StubContext) is stub_context_2
            assert active(StubDerivedContext) is stub_context_2

        assert active(StubContext) is stub_context_1
        with pytest.raises(RuntimeError, match="Cannot cast an object of type StubContext to type StubDerivedContext"):
            assert active(StubDerivedContext) is stub_context_1

    # Ensure current context is not leaked outside 'with' clauses after the test
    assert active_or_none(StubContext) is None

    with pytest.raises(RuntimeError, match="invoked outside"):
        # Ensure calling active(...) outside 'with' clause raises
        active(StubContext)


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

    # Ensure current context is not leaked outside 'with' clauses before the test
    assert active_or_none(StubContext) is None
    await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)

    with pytest.raises(RuntimeError):
        # Ensure that current context is not leaked outside the 'with clause' before the test
        active(StubContext)

    stub_context_1 = StubContext(id="stub_context_1").build()
    with activate(stub_context_1):

        await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
        assert active(StubContext) is stub_context_1

        stub_context_2 = StubDerivedContext(derived_field="stub_context_2").build()
        with activate(stub_context_2):
            await _sleep_async(task_index=task_index, rnd=rnd, max_sleep_duration=max_sleep_duration)
            assert active(StubContext) is stub_context_2
            assert active(StubDerivedContext) is stub_context_2

        assert active(StubContext) is stub_context_1
        with pytest.raises(RuntimeError, match="Cannot cast an object of type StubContext to type StubDerivedContext"):
            assert active(StubDerivedContext) is stub_context_1

    # Ensure current context is not leaked outside 'with' clauses after the test
    assert active_or_none(StubContext) is None

    with pytest.raises(RuntimeError, match="invoked outside"):
        # Ensure calling active(...) outside 'with' clause raises
        active(StubContext)


async def _gather(context_snapshot_json: str, rnd: Random):
    """Gather async functions."""
    with ContextSnapshot.from_json(context_snapshot_json):
        tasks = [_perform_testing_async(task_index=i, rnd=rnd) for i in range(TASK_COUNT)]
        await asyncio.gather(*tasks)


def test_activate():
    """Test activate method."""
    with activate(StubContext(id="0").build()) as stub_context_0:
        with activate(StubContext(id="1").build(), context_id="1") as stub_context_1:
            assert stub_context_0.id == "0"
            assert stub_context_1.id == "1"
            assert active(StubContext) is stub_context_0
            assert active(StubContext, context_id="1") is stub_context_1
        assert active_or_none(StubContext) is stub_context_0
        assert active_or_none(StubContext, context_id="1") is None
    assert active_or_none(StubContext) is None
    assert active_or_none(StubContext, context_id="1") is None


def test_activate_or_none():
    """Test activate_or_none method."""

    # Invoke with contexts
    with activate_or_none(StubContext(id="0").build()) as stub_context_0:
        with activate_or_none(StubContext(id="1").build(), context_id="1") as stub_context_1:
            assert stub_context_0.id == "0"
            assert stub_context_1.id == "1"
            assert active(StubContext) is stub_context_0
            assert active(StubContext, context_id="1") is stub_context_1
        assert active_or_none(StubContext) is stub_context_0
        assert active_or_none(StubContext, context_id="1") is None
    assert active_or_none(StubContext) is None
    assert active_or_none(StubContext, context_id="1") is None

    # Invoke with None - should have no-op behavior
    with activate_or_none(None) as result:
        assert result is None
        # Should not affect any active contexts
        assert active_or_none(StubContext) is None
    
    # Test that None with context_id raises error
    with pytest.raises(RuntimeError, match="If context is None, context_id must also be None"):
        with activate_or_none(None, context_id="test"):
            pass


def test_make_active():
    """Test make_active and make_inactive methods."""

    # Test basic make_active and make_inactive functionality
    stub_context_0 = StubContext(id="0").build()
    stub_context_1 = StubContext(id="1").build()

    # Ensure no active context initially
    assert active_or_none(StubContext) is None
    assert active_or_none(StubContext, context_id="1") is None

    # Activate first context
    make_active(stub_context_0)
    assert active(StubContext) is stub_context_0
    assert active_or_none(StubContext, context_id="1") is None

    # Activate second context with different context_id
    make_active(stub_context_1, context_id="1")
    assert active(StubContext) is stub_context_0
    assert active(StubContext, context_id="1") is stub_context_1

    # Deactivate contexts in reverse order
    make_inactive(stub_context_1, context_id="1")
    assert active(StubContext) is stub_context_0
    assert active_or_none(StubContext, context_id="1") is None

    make_inactive(stub_context_0)
    assert active_or_none(StubContext) is None
    assert active_or_none(StubContext, context_id="1") is None

    # Test nested activation with different context types
    stub_context_2 = StubDerivedContext(derived_field="stub_context_2").build()

    # Activate base context
    make_active(stub_context_0)
    assert active(StubContext) is stub_context_0

    # Activate derived context
    make_active(stub_context_2)
    assert active(StubContext) is stub_context_2
    assert active(StubDerivedContext) is stub_context_2

    # Deactivate derived context
    make_inactive(stub_context_2)
    assert active(StubContext) is stub_context_0
    with pytest.raises(RuntimeError, match="Cannot cast an object of type StubContext to type StubDerivedContext"):
        active(StubDerivedContext)

    # Deactivate base context
    make_inactive(stub_context_0)
    assert active_or_none(StubContext) is None

    # Test error handling - trying to deactivate when no context is active
    with pytest.raises(RuntimeError, match="has been cleared inside"):
        make_inactive(stub_context_0)

    # Test error handling - trying to deactivate wrong context
    make_active(stub_context_0)
    with pytest.raises(RuntimeError, match="has been changed bypassing the context manager"):
        make_inactive(stub_context_1)  # Different context object
    make_inactive(stub_context_0)  # Clean up
    
def test_error_handling():
    """Test error handling in specifying extensions."""

    stub_context_1 = StubContext(id="stub_context_1").build()
    stub_context_2 = StubDerivedContext(id="stub_context_2").build()

    # Outer context all of the fields of the inner context, ok
    assert active_or_none(StubContext) is None
    with activate(stub_context_1):
        with activate(stub_context_2):
            pass
    assert active_or_none(StubContext) is None

    # Outer context raises on __post__init__
    with pytest.raises(RuntimeError):
        with activate(StubContext(error_on_post_init=True).build()):
            with activate(stub_context_1):
                pass
    assert active_or_none(StubContext) is None

    # Inner context raises on __post__init__
    with pytest.raises(RuntimeError):
        with activate(stub_context_1):
            with activate(StubContext(error_on_post_init=True).build()):
                pass
    assert active_or_none(StubContext) is None

    # Outer context raises on init
    with pytest.raises(RuntimeError):
        with activate(StubContext(error_on_init=True).build()):
            with activate(stub_context_1):
                pass
    assert active_or_none(StubContext) is None

    # Inner context raises on init
    with pytest.raises(RuntimeError):
        with activate(stub_context_1):
            with activate(StubContext(error_on_init=True).build()):
                pass
    assert active_or_none(StubContext) is None

    # Outer context raises on enter
    with pytest.raises(RuntimeError):
        with activate(StubContext(error_on_enter=True).build()):
            with activate(stub_context_1):
                pass
    assert active_or_none(StubContext) is None

    # Inner context raises on enter
    with pytest.raises(RuntimeError):
        with activate(stub_context_1):
            with activate(StubContext(error_on_enter=True).build()):
                pass
    assert active_or_none(StubContext) is None

    # Outer context raises on exit
    with pytest.raises(RuntimeError):
        with activate(StubContext(error_on_exit=True).build()):
            with activate(stub_context_1):
                pass
    assert active_or_none(StubContext) is None

    # Inner context raises on exit
    with pytest.raises(RuntimeError):
        with activate(stub_context_1):
            with activate(StubContext(error_on_exit=True).build()):
                pass
    assert active_or_none(StubContext) is None


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

    # Capture active contexts and serialize to JSON
    context_snapshot_json = ContextSnapshot().capture_active().to_json()

    # Create a local random instance with seed
    rnd = Random(0)

    # Run using cooperative multitasking (asyncio)
    asyncio.run(_gather(context_snapshot_json, rnd))


if __name__ == "__main__":
    pytest.main([__file__])
