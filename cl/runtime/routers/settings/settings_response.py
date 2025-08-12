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

import importlib
import os
from dataclasses import field
from pydantic import BaseModel
from typing import Self
from cl.runtime._version import __api_schema_version__
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.for_dataclasses.extensions import optional
from cl.runtime.routers.settings.env_info import EnvInfo
from cl.runtime.settings.env_settings import EnvSettings


def _collect_package_versions() -> dict[str, str]:
    """
    Collects versions of all packages listed in EnvSettings.

    Returns:
        dict: Mapping of package names to their version strings.
    """
    result = {}
    packages = EnvSettings.instance().env_packages

    for package in packages:
        version = "0.1.0"  # TODO: Use another code for the default version
        try:
            version = importlib.metadata.version(package)
        except Exception:
            module = importlib.import_module(package)
            if hasattr(module, "__version__") and module.__version__:
                version = str(module.__version__)
        result[package] = version

    return result


def _get_envs() -> list[EnvInfo]:
    """Return stub envs."""
    return [EnvInfo(name="Dev;Runtime;V2", parent="")]  # TODO: Use Dynaconf for the default


class SettingsResponse(BaseModel):
    """
    Response model for the /settings route.

    Provides application metadata, environment, component versions, event transport type,
    and a list of configured data sources.
    """

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    schema_version: str = __api_schema_version__
    """Version of the backend-frontend API contract (schema). Used to ensure compatibility between backend and frontend."""

    # TODO: Switch to the standard design pattern using Dynaconf
    application_name: str | None = optional(default_factory=lambda: os.environ.get("CL_APP_TITLE"))
    """Name of the application."""

    # TODO: Switch to the standard design pattern using Dynaconf
    environment: str | None = optional(default_factory=lambda: os.environ.get("CL_ENVIRONMENT"))
    """
    Active application environment (e.g., 'dev', 'staging', 'prod').
    If specified, displayed as a badge in the UI header to the right of the app logo.
    """

    versions: dict[str, str] | None = field(default_factory=_collect_package_versions)
    """Dictionary of component/package names and their versions."""

    event_transport: str = "SSE"
    """
    Server event transport mechanism used for frontend-backend event communication.
    Supported types: 'SSE', 'NO_SSE'.
    """

    # TODO: DEPRECATED. Will be removed in the next iteration.
    # TODO: Use Dynaconf for the default
    sources: list[EnvInfo] | None = optional(default_factory=lambda: [EnvInfo(name="Dev;Runtime;V2", parent="")])
    """
    DEPRECATED. Will be removed in the next iteration.
    List of data sources configured for the application.
    """

    chat_about_on: bool = False
    """
    Enables or disables the 'Chat About' feature.
    When True, users can engage in context-aware dialogue with AI Chatbot based on UI focus.
    """

    demo_mode: bool = False
    """
    Activates demo mode for presentations or testing.
    May limit error reporting functionality.
    """

    dataset_support: bool = False
    """
    Enables dataset integration and manipulation features.
    When True, the UI will display dataset selection controls
    otherwise, all dataset-related features are hidden.
    """

    refresh_on_all_handlers: bool = False
    """
    Automatically refreshes the main data grid after any successful handler execution.
    Useful for keeping the UI up-to-date, but may introduce performance overhead in data-heavy environments.
    """

    grid_max_lines: int = 20
    """
    Defines the maximum number of visible lines per cell in the main grid.
    This controls how much multiline content in a single cell is immediately shown.
    """

    hide_empty_columns: bool = True
    """
    When enabled, automatically hides columns in the grid that have no data across all rows.
    This reduces visual clutter and improves data focus, especially in sparse datasets.
    """

    hide_handlers_in_full_screen_mode: bool = False
    """
    Controls whether handlers controls are hidden in full-screen mode.

    When set to True, handler UIs will be suppressed during full-screen mode,
    allowing for cleaner focus on primary content areas. This is useful in streamlined UIs.

    When False, handler interfaces remain visible and accessible even in full-screen mode.
    """

    @classmethod
    def get_response(cls) -> Self:
        """Return settings response."""
        return cls()
