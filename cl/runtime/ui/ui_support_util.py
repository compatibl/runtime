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

import io
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.log.log_message import LogMessage
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.settings.log_settings import LogSettings
from cl.runtime.ui.ui_app_state import UiAppState

BASE_LOG_DIR: Path = Path(LogSettings.get_log_dir())


@dataclass(slots=True, kw_only=True)
class UiSupportUtil(DataclassMixin):
    """
    Utility type to provide support-related functionality.
    """

    @classmethod
    def run_save_frontend_error(cls, error: str) -> None:
        """Save frontend error as `LogMessage` record."""
        entry = LogMessage(message=error, level="Error").build()
        active(DataSource).replace_one(entry, commit=True)

    @classmethod
    def run_get_feedback_form_details(cls):
        """Returns settings data for filling feedback form to frontend."""
        raise NotImplementedError("Feedbacks are currently not supported.")

    @classmethod
    def run_send_feedback(
        cls,
        subject: str,
        body: str,
        include_logs: bool,
        email_to: list[str] = None,
        attachments: list[FileData] | None = None,
    ):
        """Send feedback email with attachments and logs if include_logs is true."""
        raise NotImplementedError("Feedbacks are currently not supported.")

    @classmethod
    def run_download_logs(cls) -> FileData:
        """Download logs from UI."""

        app_name = cls._get_application_name()
        logs_timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        file_name_prefix = f"{app_name}-" if app_name else ""
        zip_file_name = f"{file_name_prefix}logs-{logs_timestamp}.zip"
        zip_file_name = quote(zip_file_name)  # Quoting special characters
        return cls._create_zip_archive(zip_file_name, files_to_zip=list(BASE_LOG_DIR.glob("*.log")))

    @classmethod
    def _create_zip_archive(cls, zip_file_name: str, files_to_zip: list[Path]) -> FileData:
        """Create an in-memory zip archive."""

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files_to_zip:
                file_path = Path(file_path)
                zip_file.write(file_path, arcname=file_path.name)
        zip_bytes = zip_buffer.getvalue()

        return FileData(name=zip_file_name, file_bytes=zip_bytes, file_kind=FileKind.ZIP)

    @classmethod
    def _get_application_name(cls) -> str | None:
        """Get the application name."""

        app_state_record = UiAppState.get_global_app_state()
        app_name = app_state_record.application_name if app_state_record else None
        return app_name
