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

import orjson
from fastapi import APIRouter
from fastapi import Request
from sse_starlette import EventSourceResponse
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.sse.event_broker import EventBroker

router = APIRouter()

_UI_SERIALIZER = DataSerializers.FOR_UI


async def _event_generator(request: Request):
    """Async generator of events for /events route response."""

    async with EventBroker.create() as event_broker:
        async for event in event_broker.subscribe(topic="events", request=request):

            # Serialize event and convert to JSON string because SSE protocol requires text-based 'data' field
            event_data = _UI_SERIALIZER.serialize(event)
            event_data = orjson.dumps(event_data).decode("utf-8")

            # Create dict event in format required by EventSourceResponse
            processed_event = {"event": event.event_type.name, "data": event_data}

            yield processed_event


@router.get("/events")
async def events(request: Request) -> EventSourceResponse:
    """Server event stream route."""
    return EventSourceResponse(_event_generator(request))
