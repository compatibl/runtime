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
import logging.config
from unittest.mock import patch
import orjson
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
from cl.runtime.events.event import Event
from cl.runtime.events.event_kind import EventKind
from cl.runtime.log.log_config import logging_config
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.routers.server_util import ServerUtil
from cl.runtime.routers.sse.sse_router import _event_generator as original_event_generator  # noqa

_LOGGER = logging.getLogger(__name__)

_test_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_test_event_loop)


async def _listen_events(client):
    headers = {"Accept": "text/event-stream"}

    async with client.stream("GET", "/sse/events", headers=headers) as response:
        assert response.status_code == 200
        event_stream_lines = []
        async for line in response.aiter_lines():
            event_stream_lines.append(line)

        return event_stream_lines


async def _publish_events(client):
    await asyncio.sleep(0.3)
    _LOGGER.info("1 - Info")
    await asyncio.sleep(0.1)
    _LOGGER.info("2 - Info", extra={"event": Event(event_kind=EventKind.TASK_STARTED)})
    await asyncio.sleep(0.3)
    _LOGGER.warning("3 - Warning")
    await asyncio.sleep(0.2)
    _LOGGER.error("4 - Error")
    await asyncio.sleep(0.1)
    _LOGGER.info("5 - Info", extra={"event": Event(event_kind=EventKind.TASK_FINISHED)})

    # Ensure reaching limit in event generator to avoid timeout error
    for i in range(10):
        _LOGGER.info(f"Event to reach limit - #{i}.")


async def _publish_and_listen_events(listeners_count: int):
    app = FastAPI()
    ServerUtil.include_routers(app)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        listen_tasks = (_listen_events(client),) * listeners_count
        *listen_results, _ = await asyncio.gather(*listen_tasks, _publish_events(client))

        return listen_results


async def mock_event_generator_limited(request):

    max_events = 10
    count = 0
    async for event in original_event_generator(request):
        yield event
        count += 1
        if count >= max_events:
            break


def _parse_stream_lines(stream_lines: list[str]) -> list[dict]:
    """Parse event stream lines to list of event dicts."""
    events = []
    event = {}

    for line in stream_lines:
        line = line.strip()
        if not line:
            if event:  # end of event block
                events.append(event)
                event = {}
            continue

        if ":" in line:
            key, value = line.split(":", 1)

            if key == "data":
                data_dict = orjson.loads(value)
                value = data_dict.get("Message", "")

            event[key.strip()] = value.strip()

    # Add last event if not followed by empty line
    if event:
        events.append(event)

    return events


def test_events(default_db_fixture):

    with patch("cl.runtime.routers.sse.sse_router._event_generator", mock_event_generator_limited):
        # Run coroutines to publish and listen events in parallel asynchronously
        listen_results = _test_event_loop.run_until_complete(asyncio.wait_for(_publish_and_listen_events(1), timeout=10.0))
        assert len(listen_results) == 1

        event_stream_lines = listen_results[0]
        event_stream_data = _parse_stream_lines(event_stream_lines)

        # Verify output
        RegressionGuard().write(event_stream_data)
        RegressionGuard().verify_all()


def test_events_multi_listener(default_db_fixture):

    with patch("cl.runtime.routers.sse.sse_router._event_generator", mock_event_generator_limited):
        # Run coroutines to publish and listen events in parallel asynchronously
        listen_results = _test_event_loop.run_until_complete(asyncio.wait_for(_publish_and_listen_events(10), timeout=10.0))
        assert len(listen_results) == 10

        assert all(listen_result and listen_result == listen_results[0] for listen_result in listen_results)


if __name__ == "__main__":
    pytest.main([__file__])
