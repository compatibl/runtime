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

import logging
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator
from typing import Self
from fastapi import Request
from cl.runtime.db.tenant import Tenant
from cl.runtime.db.tenant_key import TenantKey
from cl.runtime.events.event import Event
from cl.runtime.events.event_broker_key import EventBrokerKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.data_mixin import TDataDict
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin

_logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class EventBroker(EventBrokerKey, RecordMixin, ABC):
    """Event Broker class for publishing and subscribing events."""

    tenant: TenantKey = required()
    """Tenant within the EventBroker (initialized to the common tenant if not specified)."""

    def get_key(self):
        return EventBrokerKey(broker_id=self.broker_id)

    def __init(self):
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.broker_id is None:
            self.broker_id = Timestamp.create()

        if self.tenant is None:
            self.tenant = Tenant.get_common()

    @classmethod
    def create(cls, *, tenant: TenantKey | None = None) -> Self:
        """Factory method to create Event Broker from settings."""

        from cl.runtime.events.db_event_broker import DbEventBroker

        # TODO (Roman): Get event broker type from settings.
        broker_type = DbEventBroker

        return broker_type(tenant=tenant).build()

    @abstractmethod
    async def subscribe(self, topic: str, request: Request | None = None) -> AsyncGenerator[TDataDict, None]:
        """
        Subscribe to a topic/channel. Return an async generator yielding events.
        Don't use active(...) inside the subscribe() method, as it will be executed in a separate async task.
        Isolated endpoint context created with Depends(...) will be unavailable.
        """
        raise NotImplementedError

    @abstractmethod
    async def publish(self, topic: str, event: Event) -> None:
        """Publish an Event to a topic/channel."""
        raise NotImplementedError

    def sync_publish(self, topic: str, event: Event) -> None:
        """Publish an Event to a topic/channel synchronously."""
        raise NotImplementedError

    def __enter__(self):
        """Enter the sync context. Called during the make_active() method."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit the sync context. Called during the make_inactive() method."""
        return None
