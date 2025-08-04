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
from typing import Coroutine
from starlette.requests import Request
from cl.runtime.contexts.data_context import DataContext
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.sse.event import Event
from cl.runtime.sse.event_broker import EventBroker
from cl.runtime.sse.sse_query_util import SseQueryUtil

_PULL_EVENTS_DELAY = 5.0
"""Delay in seconds to check new events in DB."""


def _handle_async_task_exception(task: asyncio.Task):
    """Log error if pull events task failed."""
    _logger = logging.getLogger(__name__)

    try:
        task.result()
    except Exception:
        _logger.error("DB SSE pull events task failed.", exc_info=True)


class DbEventBroker(EventBroker):
    """
    Event broker that uses current DataContext as transport for events.
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

        # Background async task to pull events from the database
        # Pulling starts when the subscribe() method is called
        self._pull_events_task: Coroutine[None, None, None] | None = None

    async def connect(self) -> None:
        return None

    async def subscribe(self, topic: str, request: Request | None = None) -> AsyncGenerator[Event, None]:

        # Start pulling events from db in parallel async task
        if self._pull_events_task is None:
            pull_events_task = asyncio.create_task(self._pull_events())
            pull_events_task.add_done_callback(_handle_async_task_exception)
            self._pull_events_task = pull_events_task

        # Yield events from base subscribe() implementation
        async for event in super(DbEventBroker, self).subscribe(topic=topic, request=request):
            yield event

    async def _get_event(self) -> Event:
        # Await event in queue
        return await self._event_queue.get()

    async def publish(self, topic: str, event: Event) -> None:
        return self.sync_publish(topic, event)

    def sync_publish(self, topic: str, event: Event) -> None:
        # Publish event by just saving to DB
        DataContext.save_one(event)

    async def close(self) -> None:
        # Cancel pull events task
        if self._pull_events_task is not None:
            self._pull_events_task.cancel()

    async def _pull_events(self):
        _logger = logging.getLogger(__name__)

        while True:
            # Get unprocessed events from the DB, sorted by ascending timestamp
            # TODO (Roman): Replace with DataContext.query() when supported
            new_events = self._get_unprocessed_events()

            if new_events:
                _logger.debug(f"SSE: Found {len(new_events)} events in DB.")

            # Put events to queue
            for event in new_events:
                await self._event_queue.put(event)

            await asyncio.sleep(_PULL_EVENTS_DELAY)

    def _get_unprocessed_events(self) -> list[Event]:
        """Get unprocessed events and mark them as processed."""

        sent_event_set = set(self._sent_event_buffer)

        # Query DB with limit and exclude already sent events
        unprocessed_events = list(
            reversed(
                [
                    x
                    for x in SseQueryUtil.query_sorted_desc_and_limited(Event().get_table(), limit=100)
                    if x.timestamp > self._from_timestamp and x.timestamp not in sent_event_set
                ]
            )
        )

        self._sent_event_buffer.extend((x.timestamp for x in unprocessed_events))

        return unprocessed_events
