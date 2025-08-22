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

import asyncio
import logging
from collections import deque
from typing import AsyncGenerator
from starlette.requests import Request
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.events.event import Event
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.events.sse_query_util import SseQueryUtil
from cl.runtime.primitive.timestamp import Timestamp

_LOGGER = logging.getLogger(__name__)

_PULL_EVENTS_DELAY = 3.0
"""Delay in seconds to check new events in DB."""


def _handle_async_task_exception(task: asyncio.Task):
    """Log error if pull events task failed."""

    try:
        task.result()
    except asyncio.CancelledError:
        # Ignore task canceled error
        pass
    except Exception:
        _LOGGER.error("DB SSE pull events task failed.", exc_info=True)


async def _pull_events(queue: asyncio.Queue):
    while True:
        # Get unprocessed events from the DB, sorted by ascending timestamp
        # TODO (Roman): Replace with DataSource.query() when supported
        new_events = list(
            reversed([x for x in SseQueryUtil.query_sorted_desc_and_limited(Event().get_key_type(), limit=100)])
        )

        # Put events to subscribed queues
        for event in new_events:
            await queue.put(event)

        # Wait for delay
        await asyncio.sleep(_PULL_EVENTS_DELAY)


class DbEventBroker(EventBroker):
    """
    Event broker that uses current DataSource as transport for events.
    Constantly checks if there are new events in the DB and sends them to the queue.
    """

    _event_type: type = Event
    """Type of event records."""

    _event_buffer_maxlen: int = 100
    """Max number of sent events in buffer."""

    def __init__(self):
        # Buffer queue for sent events
        self._sent_event_buffer: deque[str] = deque(maxlen=self._event_buffer_maxlen)

        # Set start timestamp for filtering old events
        self._from_timestamp = Timestamp.create()

        # Buffer queue for event
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()

        # Async Task for pulling Events from DB.
        self._pull_events_task: asyncio.Task | None = None

    async def connect(self) -> None:
        return None

    async def subscribe(self, topic: str, request: Request | None = None) -> AsyncGenerator[Event, None]:

        # Start pulling events from db in parallel async task
        if self._pull_events_task is None:
            pull_events_task = asyncio.create_task(_pull_events(self._event_queue))
            pull_events_task.add_done_callback(_handle_async_task_exception)
            self._pull_events_task = pull_events_task

        # Yield events from base subscribe() implementation
        async for event in super(DbEventBroker, self).subscribe(topic=topic, request=request):
            yield event

    async def _get_event(self) -> Event:
        # Await event in queue
        while True:
            event = await self._event_queue.get()

            # Filter old or already sent events
            if event.timestamp > self._from_timestamp and event.timestamp not in self._sent_event_buffer:
                self._sent_event_buffer.append(event.timestamp)
                return event

    async def publish(self, topic: str, event: Event) -> None:
        return self.sync_publish(topic, event)

    def sync_publish(self, topic: str, event: Event) -> None:
        # Publish event by just saving to DB
        active(DataSource).replace_one(event, commit=True)

    async def close(self) -> None:
        # Cancel pull events task
        if self._pull_events_task is not None:
            self._pull_events_task.cancel()
