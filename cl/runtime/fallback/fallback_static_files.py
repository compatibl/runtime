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

from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.types import Scope, Receive, Send
from starlette.exceptions import HTTPException
from cl.runtime.settings.frontend_settings import FrontendSettings

_FALLBACK_HTML= """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Install frontend files for CompatibL UI</title>
    <link rel="stylesheet" href="./css/styles.css">
</head>
<body>

<main class="main">
    <div class="logo">
        <img src="./images/logo-full.png" alt="CompatibL Logo" />
    </div>
    <section class="card">
        <h1>Static frontend files for CompatibL UI are not installed</h1>
        <p class="subtitle">Installation options</p>
        <hr />
        <ul>
            <li>
                Option 1
                <ul>
                    <li>
                        Execute '__main__.py' from Python or 'run_backend.cmd/sh' from the command line
                    </li>
                    <li>
                        Type 'yes' when prompted to confirm static frontend files download
                    </li>
                </ul>
            </li>
            <li>
                Option 2
                <ul>
                    <li>
                        Download static frontend files as a ZIP archive:
                        <a href="https://github.com/compatibl/frontend/archive/refs/tags/{version}.zip">frontend-{version}.zip</a>
                    </li>
                    <li>
                        Place the directory 'static' from the archive under the project root
                    </li>
                </ul>
            </li>
        </ul>
    </section>
</main>
</body>
</html>
"""

_FALLBACK_DIR = os.path.dirname(os.path.abspath(__file__))

class FallbackStaticFiles(StaticFiles):
    """Static files handler that serves a fallback index.html page when directory 'static' is not found."""

    def __init__(self):
        """Parameters for the fallback page."""
        super().__init__(directory=_FALLBACK_DIR, html=False)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Generate index.html dynamically."""
        path = scope.get("path", "")
        if path == "" or path == "/" or path == "/index.html":
            response = HTMLResponse(content=self.get_fallback_html())
            await response(scope, receive, send)
        else:
            await super().__call__(scope, receive, send)

    @classmethod
    def get_fallback_html(cls) -> str:
        """Return the index.html content dynamically."""
        if (version := FrontendSettings.instance().frontend_version) is not None:
            return _FALLBACK_HTML.format(version=version)
        else:
            raise RuntimeError(
                f"Cannot install frontend static files because frontend_version is not found in settings.yaml."
            )
