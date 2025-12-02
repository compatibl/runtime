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
from cl.runtime.contexts.context_manager import active_or_default
from cl.runtime.db.tenant import Tenant
from cl.runtime.db.tenant_key import TenantKey
from cl.runtime.events.event import Event
from cl.runtime.events.event_broker_key import EventBrokerKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.data_mixin import TDataDict
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.server.env import Env
from cl.runtime.settings.sse_settings import SseSettings

_logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class EventBroker(EventBrokerKey, RecordMixin, ABC):
    """Event Broker class for publishing and subscribing events."""

    tenant: TenantKey = required()
    """Tenant within the EventBroker (initialized to the common tenant if not specified)."""

    def get_key(self):
        return EventBrokerKey(broker_id=self.broker_id)

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.broker_id is None:
            self.broker_id = Timestamp.create()

        if self.tenant is None:
            self.tenant = Tenant.get_common()

    @classmethod
    def create(
        cls, *, broker_type: type | None = None, broker_id: str | None = None, tenant: TenantKey | None = None
    ) -> Self:
        """Factory method to create Event Broker from settings."""

        sse_settings = SseSettings.instance()

        # Get Broker type from settings
        if broker_type is None:
            broker_type = TypeInfo.from_type_name(sse_settings.sse_broker_type)

        # Get Broker id from settings if it is not test
        if broker_id is None:
            if not active_or_default(Env).is_test():
                broker_id = sse_settings.sse_broker_id
            else:
                raise RuntimeError("Use pytest fixtures to create temporary EventBroker inside tests.")

        return broker_type(broker_id=broker_id, tenant=tenant).build()

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

    @abstractmethod
    def drop_test_broker(self) -> None:
        """
        Drop a EventBroker as part of a unit test.

        EVERY IMPLEMENTATION OF THIS METHOD MUST FAIL UNLESS THE FOLLOWING CONDITIONS ARE MET:
        - The method is invoked from a unit test based on active_or_default(Env).testing
        - broker_id starts with sse_test_prefix specified in settings.yaml (the default prefix is 'test_')
        """
        raise NotImplementedError

    def check_drop_test_broker_preconditions(self) -> None:
        """Error if broker_id does not start from sse_test_prefix specified in settings.yaml (defaults to 'test_')."""
        if not active_or_default(Env).is_test():
            raise RuntimeError(f"Cannot drop a unit test EventBroker when not invoked from a running unit test.")

        sse_settings = SseSettings.instance()
        if not self.broker_id.startswith(sse_settings.sse_test_prefix):
            raise RuntimeError(
                f"Cannot drop a unit test EventBroker from code because its broker_id={self.broker_id}\n"
                f"does not start from unit test EventBroker prefix '{sse_settings.sse_test_prefix}'."
            )
