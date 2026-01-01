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

import logging
import os
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from typing_extensions import final  # TODO: Replace by the import from typing
from cl.runtime.contexts.os_util import OsUtil
from cl.runtime.file.project_layout import ProjectLayout
from cl.runtime.prebuild.version_util import VersionUtil
from cl.runtime.settings.settings import Settings

_logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
@final
class FrontendSettings(Settings):
    """Settings that apply to the static frontend files."""

    frontend_version: str | None = None
    """Install a specific frontend version in MAJOR.MINOR.MICRO format."""

    frontend_dir: str = "frontend-{version}"
    """
    Directory template for the location of index.html relative to project root.

    Notes:
        - May include {version}, in which case the specified frontend_version will be substituted
    """

    frontend_download_uri: str = "https://github.com/compatibl/frontend/archive/refs/tags/{version}"
    """
    URI template for frontend download.
    
    Notes:
        - May include {version}, in which case the specified frontend_version will be substituted
        - If file extension is omitted, .zip and .tar.gz choices will be provided
    """

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Validate that version string is in CompatibL CalVer format if specified
        if self.frontend_version is not None:
            VersionUtil.guard_module_version(version=self.frontend_version, module="Frontend")
        else:
            if "{frontend_version}" in self.frontend_dir:
                raise RuntimeError("Field frontend_dir contains {frontend_version} which is not specified.")
            if "{frontend_version}" in self.frontend_download_uri:
                raise RuntimeError("Field frontend_download_uri contains {frontend_version} which is not specified.")

    def get_frontend_download_uri_choices(self) -> tuple[str, ...]:
        """Get the list of frontend URI choices for the specified template."""

        # Substitute version into the download URI template
        base_uri = self.frontend_download_uri.format(frontend_version=self.frontend_version)

        # Provide both .zip and .tar.gz choices if extension is not specified in the template
        if base_uri.endswith(".zip") or base_uri.endswith(".tar.gz"):
            # Extension is specified, return a single choice
            return (base_uri,)
        else:
            # Return both .zip and .tar.gz choices
            return (
                base_uri + ".zip",
                base_uri + ".tar.gz",
            )

    def get_frontend_download_uri_preferred_choice(self) -> str:
        """Get the preferred frontend URIs choice for the specified template and the current OS."""

        # Substitute version into the download URI template
        base_uri = self.frontend_download_uri.format(frontend_version=self.frontend_version)

        # Provide both .zip and .tar.gz choices if extension is not specified in the template
        if base_uri.endswith(".zip") or base_uri.endswith(".tar.gz"):
            return base_uri
        else:
            # Extension is specified, select based on OS type
            if OsUtil.is_windows():
                return base_uri + ".zip"
            else:
                return base_uri + ".tar.gz"

    def get_index_file_path(self) -> str:
        """
        Return path to index.html file in frontend static files dir.

        index.html file must be located in the 'project_root/frontend-{version}' folder if the version is specified,
        or in the 'project_root/frontend' folder if the version is not specified.
        """
        # Get project root
        project_root = ProjectLayout.get_project_root()

        # Substitute version into the frontend_dir
        frontend_dir = self.frontend_dir.format(frontend_version=self.frontend_version)

        # Join paths to get path to index.html file
        return os.path.join(project_root, frontend_dir, "static", "index.html")

    def is_frontend_installed(self) -> bool:
        """Check if frontend is installed by presence of index.html file in frontend static files dir."""
        index_file_path = self.get_index_file_path()
        return os.path.exists(index_file_path) and os.path.isfile(index_file_path)

    def install_frontend(self) -> None:
        """Download frontend archive from GitHub and extract to project root."""

        # Get frontend path as the second parent of the index.html file
        frontend_path = os.path.dirname(os.path.dirname(self.get_index_file_path()))

        if self.is_frontend_installed():
            # If frontend installed, nothing to do
            return
        elif os.path.exists(frontend_path) and os.listdir(frontend_path):
            # If frontend is not installed but directory is not empty, raise error
            raise RuntimeError(f"Frontend directory '{frontend_path}' exists but it is not valid frontend.")

        # Raise error if frontend_version is not specified
        if self.frontend_version is None:
            raise RuntimeError(
                "Cannot install frontend because the frontend version is missing.\n"
                "Please specify 'frontend_version' in settings.yaml."
            )

        # Get download URI
        uri = self.get_frontend_download_uri_preferred_choice()

        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, "frontend_archive")

            # Download archive to temp dir
            try:
                _logger.info(f"Downloading frontend archive from {uri}.")
                with urllib.request.urlopen(uri) as response, open(archive_path, "wb") as f:
                    shutil.copyfileobj(response, f)
            except urllib.error.HTTPError as exc:
                # Handle case when archive not found
                if exc.code == 404:
                    raise RuntimeError(f"Frontend archive not found (404): {uri}") from exc
                raise RuntimeError(f"HTTP error while downloading {uri}: {exc.code}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Failed to reach URL {uri}: {exc.reason}") from exc

            extract_path = os.path.join(tmp_dir, "extract")
            # Detect archive type and extract to project root
            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path) as zip_file:
                    top_archive_level = self._get_zip_top_level_name(zip_file)
                    zip_file.extractall(extract_path)
            elif tarfile.is_tarfile(archive_path):
                with tarfile.open(archive_path) as tar_file:
                    top_archive_level = self._get_tar_top_level_name(tar_file)
                    tar_file.extractall(extract_path)
            else:
                raise RuntimeError(
                    f"Unsupported frontend archive format downloaded from '{uri}': {os.path.basename(archive_path)}."
                )

            # Move extracted archive data to frontend_path
            extract_data_path = os.path.join(extract_path, top_archive_level)
            shutil.move(extract_data_path, frontend_path)

        # Post-install validation
        if not self.is_frontend_installed():
            raise RuntimeError(f"Frontend installation failed.")
        else:
            _logger.info(f"Frontend installation succeeded in '{os.path.dirname(self.get_index_file_path())}'.")

    @classmethod
    def _get_zip_top_level_name(cls, zip_file: zipfile.ZipFile) -> str:
        """Check that the .zip archive contains one root element and return its name."""
        top_levels = set()

        for name in zip_file.namelist():
            # Normalize and split
            parts = name.strip("/").split("/", 1)
            if parts:
                top_levels.add(parts[0])

        if len(top_levels) == 1:
            return next(iter(top_levels))
        else:
            raise RuntimeError(
                "Unexpected archive structure.\n"
                "Expected the archive to contain exactly one top-level directory "
                "(e.g. 'frontend-<version>').\n"
                f"Found top-level entries: {sorted(top_levels)}"
            )

    @classmethod
    def _get_tar_top_level_name(cls, tar_file: tarfile.TarFile) -> str:
        """Check that the .tar.gz archive contains one root element and return its name."""
        top_levels = set()

        for member in tar_file.getmembers():
            # Normalize and split
            name = member.name.strip("/")
            if not name:
                continue

            parts = name.split("/", 1)
            top_levels.add(parts[0])

        if len(top_levels) == 1:
            return next(iter(top_levels))
        else:
            raise RuntimeError(
                "Unexpected archive structure.\n"
                "Expected the archive to contain exactly one top-level directory "
                "(e.g. 'frontend-<version>').\n"
                f"Found top-level entries: {sorted(top_levels)}"
            )
