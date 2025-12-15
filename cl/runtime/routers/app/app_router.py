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

import os
from fastapi import APIRouter
from starlette.responses import RedirectResponse, HTMLResponse

from cl.runtime.fallback.fallback_static_files import FallbackStaticFiles
from cl.runtime.file.project_layout import ProjectLayout
from starlette import status

router = APIRouter()

def get_index_html_or_none() -> str | None:
    """Return the index.html content dynamically."""
    static_dir = ProjectLayout.get_static_dir()
    index_file_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file_path) and os.path.isfile(index_file_path):
        with open(index_file_path, "r", encoding="utf-8") as index_file:
            return index_file.read()
    else:
        return None

_INDEX_HTML = get_index_html_or_none()
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

    if _INDEX_HTML is not None:
        # Return index.html content for SPA routing after page refresh
        return _INDEX_HTML
    else:
        # If static files are not installed, generate fallback page
        return FallbackStaticFiles.get_fallback_html()