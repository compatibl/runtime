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
from abc import ABC
from abc import abstractmethod
from typing import AsyncGenerator
from fastapi import Request
from typing_extensions import Self
from cl.runtime.sse.event import Event
from cl.runtime.sse.event_type import EventType

_PING_DELAY = 15.0
"""Delay in seconds to send a ping event."""


class EventBroker(ABC):
    """Base class for event broker."""

    @classmethod
    def create(cls) -> Self:
        """Factory method to create event broker from settings."""

        from cl.runtime.sse.db_event_broker import DbEventBroker

        # TODO (Roman): Get event broker type from settings.
        broker_type = DbEventBroker

        return broker_type()

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the broker."""
        raise NotImplementedError

    async def subscribe(self, topic: str, request: Request | None = None) -> AsyncGenerator[Event, None]:
        """
        Subscribe to a topic/channel.
        Should return an async generator yielding events.
        """

        _logger = logging.getLogger(__name__)

        while True:
            if request and await request.is_disconnected():
                _logger.debug("SSE: Client disconnected from SSE. Stop sending events.")
                break

            try:
                # Wait for the next event from the queue
                yield await asyncio.wait_for(self._get_event(), _PING_DELAY)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                yield Event(event_type=EventType.PING).build()

    @abstractmethod
    async def _get_event(self) -> Event:
        """Get event from broker source. Wait for event if source is empty."""
        raise NotImplementedError

    @abstractmethod
    async def publish(self, topic: str, event: Event) -> None:
        """Publish an Event to a topic/channel."""
        raise NotImplementedError

    def sync_publish(self, topic: str, event: Event) -> None:
        """Publish an Event to a topic/channel synchronously."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Close connection to the broker."""
        raise NotImplementedError

    async def __aenter__(self):
        """
        Called when entering the async context manager.
        Automatically connects to the broker.
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Called when exiting the async context manager.
        Ensures a graceful shutdown by closing the broker connection.
        """
        await self.close()
