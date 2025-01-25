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

from starlette.types import ASGIApp
from cl.runtime import Db
from cl.runtime.contexts.context_manager import ContextManager
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.contexts.process_context import ProcessContext


class ContextMiddleware:
    """Middleware to wrap ProcessContext around the implementation."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        # TODO: Create a test setting to enable this other than by uncommenting
        # duration = random.uniform(0, 10)
        # print(f"Before request processing: {duration}")

        # Set ContextVar=None before async task execution, get a token for restoring its previous state
        token = ContextManager.save_and_clear_state()
        try:
            with ProcessContext().build():
                with DbContext(db=Db.create()).build():
                    # TODO: Create a test setting to enable this other than by uncommenting
                    # await asyncio.sleep(duration)
                    await self.app(scope, receive, send)
        finally:
            # Restore ContextVar to its previous state after async task execution using a token
            # from 'save_and_clear_state' whether or not an exception occurred
            ContextManager.restore_state(token)

        # TODO: Create a test setting to enable this other than by uncommenting
        # print(f"After request processing: {duration}")
