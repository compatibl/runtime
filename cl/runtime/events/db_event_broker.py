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
from dataclasses import dataclass
from typing import AsyncGenerator
from starlette.requests import Request
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.sort_order import SortOrder
from cl.runtime.events.event import Event
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.data_mixin import TDataDict
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.serializers.data_serializers import DataSerializers

_logger = logging.getLogger(__name__)

_pull_events_delay = 3.0
"""Delay in seconds to check new events in DB."""

_event_buffer_maxlen = 100
"""Max number of sent events in buffer."""


def _handle_async_task_exception(task: asyncio.Task):
    """Log error if pull events task failed."""

    try:
        task.result()
    except asyncio.CancelledError:
        # Ignore task canceled error
        pass
    except Exception:
        _logger.error("DB SSE pull events task failed.", exc_info=True)


async def _pull_events(queue: asyncio.Queue, data_source: DataSource):
    while True:
        # Get unprocessed events from the DB, sorted by ascending timestamp
        # load_all is enough as Event key field is timestamp
        new_events = data_source.load_all(key_type=Event().get_key_type(), sort_order=SortOrder.DESC, limit=100)[::-1]

        # Put events to subscribed queues
        for event in new_events:
            await queue.put(event)

        # Wait for delay
        await asyncio.sleep(_pull_events_delay)


@dataclass(slots=True, kw_only=True)
class DbEventBroker(EventBroker):
    """
    Event broker that uses current DataSource as transport for events.
    Continuously checks if there are new events in the DB and sends them to the queue.
    """

    data_source: DataSource = required()
    """Data source used for pulling events."""

    _sent_event_buffer: deque[str] | None = None
    """Buffer queue for sent events."""

    _from_timestamp: str | None = None
    """Set start timestamp for filtering old events."""

    _event_queue: asyncio.Queue[Event] | None = None
    """Buffer queue for events."""

    _pull_events_task: asyncio.Task | None = None
    """Async Task for pulling Events from DB."""

    def __init(self):

        # Set active DataSource if not specified. Use instance-level DataSource instead of active(DataSource)
        # to allow FastAPI execute streaming response generator in a separate async task
        if self.data_source is None:
            self.data_source = active(DataSource)

        if self._sent_event_buffer is None:
            self._sent_event_buffer: deque[str] = deque(maxlen=100)

        if self._from_timestamp is None:
            self._from_timestamp = Timestamp.create()

        if self._event_queue is None:
            self._event_queue: asyncio.Queue[Event] = asyncio.Queue()

        if self._pull_events_task is None:
            self._pull_events_task: asyncio.Task | None = None

    async def subscribe(self, topic: str, request: Request | None = None) -> AsyncGenerator[TDataDict, None]:

        # Start pulling events from db in parallel async task
        if self._pull_events_task is None:
            pull_events_task = asyncio.create_task(_pull_events(self._event_queue, self.data_source))
            pull_events_task.add_done_callback(_handle_async_task_exception)
            self._pull_events_task = pull_events_task

        while True:
            if request and await request.is_disconnected():
                _logger.debug("SSE: Client disconnected from SSE. Stop sending events.")
                break

            # Wait for the next event from the queue
            yield await self._get_event()

    async def _get_event(self) -> TDataDict:
        # Await event in queue
        while True:
            event = await self._event_queue.get()

            # Filter old or already sent events
            if event.timestamp > self._from_timestamp and event.timestamp not in self._sent_event_buffer:
                self._sent_event_buffer.append(event.timestamp)
                event_data = DataSerializers.FOR_UI.serialize(event)
                return event_data

    async def publish(self, topic: str, event: Event) -> None:
        return self.sync_publish(topic, event)

    def sync_publish(self, topic: str, event: Event) -> None:
        # Publish event by just saving to DB
        self.data_source.replace_one(event, commit=True)

    async def close(self) -> None:
        # Cancel pull events task
        if self._pull_events_task is not None:
            self._pull_events_task.cancel()
