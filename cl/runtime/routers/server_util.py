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

from fastapi import Depends
from fastapi import FastAPI
from cl.runtime.routers.app import app_router
from cl.runtime.routers.auth import auth_router
from cl.runtime.routers.entity import entity_router
from cl.runtime.routers.handler import handler_router
from cl.runtime.routers.health import health_router
from cl.runtime.routers.schema import schema_router
from cl.runtime.routers.settings import settings_router
from cl.runtime.routers.sse import sse_router
from cl.runtime.routers.storage import storage_router
from cl.runtime.routers.tasks import tasks_router
from cl.runtime.server.auth_dependency import activate_auth_context


class ServerUtil:
    """Configures FastAPI server app for uvicorn or test client."""

    @classmethod
    def include_routers(cls, server_app: FastAPI):
        server_app.include_router(app_router.router, prefix="", tags=["App"])
        server_app.include_router(health_router.router, prefix="", tags=["Health Check"])
        server_app.include_router(settings_router.router, prefix="", tags=["Application Settings"])
        server_app.include_router(auth_router.router, prefix="/auth", tags=["Authorization"])

        # Routers with Auth dependency
        server_app.include_router(
            sse_router.router, prefix="/sse", tags=["SSE"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            schema_router.router, prefix="/schema", tags=["Schema"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            storage_router.router, prefix="/storage", tags=["Storage"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            entity_router.router, prefix="/entity", tags=["Entity"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            tasks_router.router, prefix="/tasks", tags=["Tasks"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            handler_router.router, prefix="/handler", tags=["Handler"], dependencies=[Depends(activate_auth_context)]
        )
