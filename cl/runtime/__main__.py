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

import logging.config
import os
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from cl.runtime.configurations.preload_configuration import PreloadConfiguration
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.fallback.fallback_static_files import FallbackStaticFiles
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.log.log_config import logging_config
from cl.runtime.log.log_config import uvicorn_empty_logging_config
from cl.runtime.records.typename import typename
from cl.runtime.routers.context_middleware import ContextMiddleware
from cl.runtime.routers.server_util import ServerUtil
from cl.runtime.server.env import Env
from cl.runtime.server.shutdown_aware_server import ShutdownAwareServer
from cl.runtime.settings.api_settings import ApiSettings
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.settings.env_kind import EnvKind
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.frontend_settings import FrontendSettings
from cl.runtime.tasks.celery.celery_queue import CeleryQueue
from cl.runtime.tasks.celery.celery_queue import celery_delete_existing_tasks

# Server
server_app = FastAPI()


# Universal exception handler function
async def handle_exception(request, exc):
    """Create error response."""

    # TODO (Roman): Temporary before introduce sse.
    # Return 500 response to avoid exception handler multiple calls.
    # IMPORTANT:
    # - If UserMessage is set it will be shown to the user on toast badge and bell becomes red.
    # - Otherwise default message will be shown.
    user_message = str(exc) if isinstance(exc, UserError) else None
    return JSONResponse({"UserMessage": user_message}, status_code=500)


# Add an exception handler
@server_app.exception_handler(Exception)
async def http_exception_handler(request, exc):
    return await handle_exception(request, exc)


# Get CORSMiddleware settings defined in Dynaconf from ApiSettings
api_settings = ApiSettings.instance()
server_app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.api_allow_origins,
    allow_origin_regex=api_settings.api_allow_origin_regex,
    allow_credentials=api_settings.api_allow_credentials,
    allow_methods=api_settings.api_allow_methods,
    allow_headers=api_settings.api_allow_headers,
    expose_headers=api_settings.api_expose_headers,
    max_age=api_settings.api_max_age,
)

# Middleware for clearing contextvars and restoring their previous state after async task execution
server_app.add_middleware(ContextMiddleware)

# Add routers
ServerUtil.include_routers(server_app)

_LOGGER = logging.getLogger(__name__)


def run_backend(*, interactive: bool = False) -> None:
    """Run REST backend, request user approvals if required and interactive is true."""

    # Set up logging config
    logging.config.dictConfig(logging_config)

    with activate(Env().build()), activate(DataSource().build()), activate(EventBroker.create()):

        ds = active(DataSource)
        _LOGGER.info(f"Connected to DB type '{typename(type(ds.db))}', db_id = '{ds.db.db_id}'.")

        # Save preloads to DB and invoke run_configure for any Configuration records with autorun=True
        env_kind = EnvSettings.instance().env_kind
        if env_kind in (EnvKind.PROD, EnvKind.UAT):
            # Keep the existing DB in PROD and UAT environments, preload only if empty
            if ds.is_empty(consider_parents=False):
                _LOGGER.info("DB is empty, preloading records...")
                PreloadConfiguration().build().run_configure()
            else:
                _LOGGER.info("DB is not empty, skip preloading of records.")
        elif env_kind in (EnvKind.DEV, EnvKind.TEMP):
            # Drop the existing DB in DEV and TEMP environments and always preload
            _LOGGER.info("Dropping existing DB...")
            ds.drop_db(interactive=interactive)
            _LOGGER.info("Preloading records...")
            PreloadConfiguration().build().run_configure()
        elif env_kind == EnvKind.TEST:
            raise RuntimeError("The backend is not intended to be run for env_kind=TEST.")
        else:
            raise ErrorUtil.enum_value_error(env_kind, EnvKind)

        # TODO: !!! This only works for the Mongo celery backend
        if CelerySettings.instance().celery_is_embedded_worker:
            celery_delete_existing_tasks()

            # Start Celery workers (will exit when the current process exits)
            CeleryQueue.run_start_queue()

            # Start health monitoring for multiprocess pool
            if CelerySettings.instance().celery_multiprocess_pool:
                from cl.runtime.tasks.celery.worker_health_monitor import WorkerHealthMonitor

                WorkerHealthMonitor.start_monitoring()

        frontend_settings = FrontendSettings.instance()

        # If frontend is not installed, ask user to install it from GitHub
        if not frontend_settings.is_frontend_installed():
            print(
                f"Static frontend files of version '{frontend_settings.frontend_version}' are not installed. "
                f"Do you want to install it from GitHub? (yes/no): "
            )
            user_response = input().strip().lower()
            if user_response == "yes":
                # Install static frontend files from GitHub
                frontend_settings.install_frontend()

        if frontend_settings.is_frontend_installed():
            # Mount static frontend files if index.html is found
            index_file_path = frontend_settings.get_index_file_path()
            server_app.mount("/", StaticFiles(directory=os.path.dirname(index_file_path), html=True))
        else:
            # Otherwise generate the fallback page
            server_app.mount("/", FallbackStaticFiles())
            _LOGGER.error("Frontend static directory not found, generating the fallback page.")

        # Open new browser tab in the default browser using http protocol, will switch to https if cert is present
        webbrowser.open_new_tab(f"http://{api_settings.api_hostname}:{api_settings.api_port}")

        # Run Uvicorn using hostname and port specified by Dynaconf
        config = uvicorn.Config(
            server_app,
            host=api_settings.api_hostname,
            port=api_settings.api_port,
            log_config=uvicorn_empty_logging_config,
        )
        server = ShutdownAwareServer(config)

        try:
            server.run()
        except KeyboardInterrupt:
            pass
        finally:
            if CelerySettings.instance().celery_is_embedded_worker:
                CeleryQueue.run_stop_queue()


if __name__ == "__main__":

    # Run backend in interactive mode when invoked from the command line
    run_backend(interactive=True)
