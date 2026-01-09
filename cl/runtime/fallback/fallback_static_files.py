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
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send
from cl.runtime.settings.frontend_settings import FrontendSettings

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Install frontend files for CompatibL UI</title>
    <link rel="stylesheet" href="/css/styles.css">
</head>
<body>

<main class="main">
    <div class="logo">
        <img src="/images/logo-full.png" alt="CompatibL Logo" />
    </div>
    <section class="card">
        {instructions}
    </section>
</main>
</body>
</html>
"""

_INSTALL_HTML = """
<h1>Static frontend files v{frontend_version} are not installed</h1>
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
                Type 'yes' when prompted to confirm static front end files download
            </li>
        </ul>
    </li>
    <li>
        Option 2
        <ul>
            <li>
                Download static front end files as a zip or tar.gz archive from:{links}
            </li>
            <li>
                Place the directory 'static' from the archive under the project root
            </li>
        </ul>
    </li>
</ul>
"""

_NO_VERSION_HTML = """
<h1>Front end version is not configured in settings.yaml</h1>
<p class="subtitle">Configuration options</p>
<hr />
<ul>
    <li>
        Option 1
        <ul>
            <li>
                Specify 'frontend_version' in 'settings.yaml'
            </li>
        </ul>
    </li>
    <li>
        Option 2
        <ul>
            <li>
                Define CL_FRONTEND_VERSION environment variable
            </li>
        </ul>
    </li>
</ul>
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

        # Get instructions based on frontend_version from settings if present or request to specify
        frontend_settings = FrontendSettings.instance()
        if (frontend_version := frontend_settings.frontend_version) is not None:

            # Get the list of frontend URI choices for the specified template
            uri_choices = frontend_settings.get_frontend_download_uri_choices()
            links = "\n".join('<br><a href="{uri}">{uri}</a>'.format(uri=uri) for uri in uri_choices)
            instructions = _INSTALL_HTML.format(frontend_version=frontend_version, links=links)
        else:
            instructions = _NO_VERSION_HTML

        # Insert instructions into the fallback HTML template
        result = _FALLBACK_HTML.format(instructions=instructions)
        return result
