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
from cl.runtime.db.db import Db
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_snapshot import ContextSnapshot
from cl.runtime.db.data_source import DataSource
from cl.runtime.server.env import Env


class ContextMiddleware:
    """Middleware to wrap Env around the implementation."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        # TODO: Create a test setting to enable this other than by uncommenting
        # duration = random.uniform(0, 10)
        # print(f"Before request processing: {duration}")

        # Capture active contexts on __enter__ to clear the asynchronous environment of any
        # previously activated contexts, the original state will be restored on __exit__
        with ContextSnapshot().build():

            # Activate contexts for this call
            with activate(Env().build()):
                with activate(DataSource(db=Db.create()).build()):
                    # TODO: Create a test setting to enable this other than by uncommenting
                    # await asyncio.sleep(duration)
                    await self.app(scope, receive, send)

        # TODO: Create a test setting to enable this other than by uncommenting
        # print(f"After request processing: {duration}")
