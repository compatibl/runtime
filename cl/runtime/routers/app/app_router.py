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

from fastapi import APIRouter
from starlette.responses import RedirectResponse, HTMLResponse

from cl.runtime.fallback.fallback_static_files import FallbackStaticFiles
from starlette import status

from cl.runtime.settings.frontend_settings import FrontendSettings

router = APIRouter()

def get_index_html_or_none() -> str | None:
    """Return the index.html content dynamically."""
    frontend_settings = FrontendSettings.instance()
    if frontend_settings.is_frontend_installed():
        with open(frontend_settings.get_index_file_path(), "r", encoding="utf-8") as index_file:
            return index_file.read()
    else:
        return None

_INDEX_HTML = None
"""Content of index.html if static frontend files are installed, otherwise None."""

@router.get(
    path="/",
    description="Redirect root path to the /app endpoint.",
    response_class=RedirectResponse,
)
async def get_app_index_root():
    """
    Redirect to '/app' endpoint for the frontend app to load index.html.
    If static files are not installed, generate fallback index.html.
    """
    return RedirectResponse("/app", status_code=status.HTTP_301_MOVED_PERMANENTLY)

@router.get(
    path="/app{_:path}",
    description="Support page refresh.",
    response_class=HTMLResponse,
)
async def get_app_index(_):
    """Support page refresh by redirecting to SPA root."""

    # Use global to avoid loading index.html for every request
    global _INDEX_HTML

    if _INDEX_HTML is None:
        # If _INDEX_HTML is None, try to update it
        actual_index_html = get_index_html_or_none()

        if actual_index_html is not None:
            # Update global _INDEX_HTML and return index.html content for SPA routing after page refresh
            _INDEX_HTML = actual_index_html
            return actual_index_html
        else:
            # If static files are not installed, generate fallback page
            return FallbackStaticFiles.get_fallback_html()
    else:
        # If _INDEX_HTML is not None, return it
        return _INDEX_HTML