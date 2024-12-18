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
import contextvars
import random
from starlette.requests import Request
from starlette.types import ASGIApp
from cl.runtime import Context
from cl.runtime.context.base_context import BaseContext
from cl.runtime.context.process_context import ProcessContext


class ContextMiddleware:
    """Middleware to wrap ProcessContext around the implementation."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] in ("http", "websocket"):
            # TODO: Create a test setting to enable this other than by uncommenting
            # duration = random.uniform(0, 10)
            # print(f"Before request processing: {duration}")

            # Set ContextVar=None before async task execution, get a token for restoring its previous state
            token = BaseContext.clear_contextvar()
            try:
                with ProcessContext():
                    # TODO: Create a test setting to enable this other than by uncommenting
                    # await asyncio.sleep(duration)
                    await self.app(scope, receive, send)
            finally:
                # Restore ContextVar to its previous state after async task execution using a token
                # from 'clear_contextvar' whether or not an exception occurred
                BaseContext.restore_contextvar(token)

            # TODO: Create a test setting to enable this other than by uncommenting
            # print(f"After request processing: {duration}")
        else:
            # If it's not an http or websocket request, pass it through unchanged
            await self.app(scope, receive, send)
