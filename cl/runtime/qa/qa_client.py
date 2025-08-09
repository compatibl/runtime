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

from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing_extensions import Self
from cl.runtime.contexts.app_context import AppContext
from cl.runtime.contexts.context_manager import enter_active
from cl.runtime.contexts.context_manager import exit_active
from cl.runtime.routers.server_util import ServerUtil


class QaClient(TestClient):
    """Creates FastAPI TestClient and enters into AppContext."""

    process_context: AppContext
    """Process context is used to pass the information to out-of-process subtasks."""

    def __init__(self):
        """Initialize process_context field."""

        # Create FastAPI app and pass it to __init__ of TestClient base
        super().__init__(rest_app := FastAPI())

        # Include routers
        ServerUtil.include_routers(rest_app)

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""

        # Call '__enter__' method of base first
        TestClient.__enter__(self)

        # Create and activate AppContext
        self.process_context = enter_active(AppContext().build())

        # Return self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""

        # Deactivate AppContext
        exit_active(self.process_context, exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb)

        # Call '__exit___' method of base last
        TestClient.__exit__(self, exc_type, exc_val, exc_tb)
