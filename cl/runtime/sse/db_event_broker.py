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
from typing import AsyncGenerator
from typing import Coroutine
from starlette.requests import Request
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.sse.event import Event
from cl.runtime.sse.event_broker import EventBroker
from cl.runtime.sse.sse_query_util import SseQueryUtil

_PULL_EVENTS_DELAY = 5.0
"""Delay in seconds to check new events in DB."""

_logger = logging.getLogger(__name__)


class DbEventBroker(EventBroker):
    """
    Event broker that uses current DbContext as transport for events.
    Constantly checks if there are new events in the DB and sends them to the queue.
    """

    _event_type: type = Event
    """Type of event records."""

    def __init__(self):
        # Initial timestamp to avoid retrieving events from the past
        self._last_sent_event_timestamp: str | None = Timestamp.create()

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
            self._pull_events_task = asyncio.create_task(self._pull_events())

        # Yield events from base subscribe() implementation
        async for event in super(DbEventBroker, self).subscribe(topic=topic, request=request):
            yield event

    async def _get_event(self) -> Event:
        # Await event in queue
        return await self._event_queue.get()

    async def publish(self, topic: str, event: Event) -> None:
        # Publish event by just saving to DB
        DbContext.save_one(event)

    async def close(self) -> None:
        # Cancel pull events task
        if self._pull_events_task is not None:
            self._pull_events_task.cancel()

    async def _pull_events(self):
        _logger.info("SSE: Start pulling events from DB.")
        while True:
            # Get events from the DB saved after the last sent timestamp, sorted by descending timestamp
            # TODO (Roman): Replace with DbContext.query() when supported
            new_events = list(
                SseQueryUtil.load_from_timestamp(self._event_type, from_timestamp=self._last_sent_event_timestamp)
            )

            if new_events:
                _logger.info(f"SSE: Found {len(new_events)} events in DB.")

            # Put events to queue in reversed (historical) order
            for event in reversed(new_events):
                await self._event_queue.put(event)
                self._last_sent_event_timestamp = event.timestamp

            _logger.info("SSE: Wait event pulling delay.")
            await asyncio.sleep(_PULL_EVENTS_DELAY)
