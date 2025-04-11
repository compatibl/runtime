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

from dataclasses import dataclass
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobClient, BlobServiceClient, ContentSettings
from typing_extensions import Self
from cl.runtime.storage.text_file import TextFile

_CONTENT_SETTINGS = ContentSettings(content_type=f'text/plain; charset=utf-8')
"""Define content settings to specify the UTF-8 encoding in blob metadata."""

@dataclass(slots=True, kw_only=True)
class AzureBlobTextFile(TextFile):
    """Provides access to Azure Blob storage via a text file API."""

    container_name: str
    """Container name (for error messages only)."""

    rel_path: str
    """Relative path to the blob in the container (for error messages only)."""

    overwrite: bool
    """Set to true for WRITE mode and to false for APPEND and READ mode."""

    _blob_client: BlobClient
    """The Azure Blob Client for the specific blob."""

    def read(self) -> str:
        """Read Azure Blob context as text."""
        self._check_lifecycle_phase()
        try:
            downloader = self._blob_client.download_blob()
            result_bytes = downloader.readall()
            result = result_bytes.decode()
            return result
        except ResourceNotFoundError:
            # Handle case where blob is not found separately
            raise RuntimeError(
                f"Azure Blob is not found in the specified container.\n"
                f"Container: {self.container_name}\nBlob: {self.rel_path}"
            ) from ResourceNotFoundError
        except Exception as exc:
            raise RuntimeError(
                f"An error occurred when reading Azure Blob\n."
                f"Container: {self.container_name}\nBlob: {self.rel_path}\nReason: {exc}"
            ) from exc

    def write(self, text: str) -> None:
        self._check_lifecycle_phase()
        try:
            # Encode the string to bytes using the specified encoding
            data_bytes = text.encode()
            self._blob_client.upload_blob(
                data=data_bytes,
                overwrite=self.overwrite,
                content_settings=_CONTENT_SETTINGS
            )
        except Exception as exc:
            raise RuntimeError(
                f"An error occurred when writing Azure Blob\n."
                f"Container: {self.container_name}\nBlob: {self.rel_path}\nReason: {exc}"
            ) from exc

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__enter__()
        self._blob_client.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__exit__(exc_type, exc_val, exc_tb)
        self._blob_client.__exit__(exc_type, exc_val, exc_tb)

