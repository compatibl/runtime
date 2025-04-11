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
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobClient
from azure.storage.blob import BlobServiceClient
from typing_extensions import Self
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.storage.binary_file import BinaryFile
from cl.runtime.storage.binary_file_mode import BinaryFileMode
from cl.runtime.storage.for_azure.azure_blob_text_file import AzureBlobTextFile
from cl.runtime.storage.storage import Storage
from cl.runtime.storage.storage_key import StorageKey
from cl.runtime.storage.text_file import TextFile
from cl.runtime.storage.text_file_mode import TextFileMode


@dataclass(slots=True, kw_only=True)
class AzureBlobStorage(Storage):
    """Provides access to Azure Blob storage using a file-based API."""

    container_name: str = required(init=False)
    """Container name using the Azure Blob service conventions."""

    _container_client: BlobServiceClient = required()
    """Azure Blob service client for the container"""

    def get_key(self) -> StorageKey:
        return StorageKey(storage_id=self.storage_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        try:
            # Create the BlobServiceClient from the connection string
            with BlobServiceClient.from_connection_string(self.connection_string) as service_client:
                service_client.get_container_client(self.container_name)

        except Exception as exc:
            # Ensure cleanup if initialization fails
            super(self.__class__, self).__exit__(type(exc), exc, exc.__traceback__)
            raise RuntimeError(f"Failed to initialize Azure Blob Service client:\nReason: {exc}") from exc

        try:
            # Create container if it does not exist
            self._container_client.create_container()
        except ResourceExistsError:
            # Do nothing if already exists
            pass

    def open_text_file(self, rel_path: str, mode: str | TextFileMode) -> TextFile:
        self._check_lifecycle_phase()
        # Get and initialize a client for the the blob
        rel_path = self._normalize_rel_path(rel_path)
        mode = self._to_text_file_mode_enum(mode)
        overwrite = mode == TextFileMode.WRITE
        blob_client = self._get_blob_client(rel_path=rel_path)
        # Create a text file instance
        return AzureBlobTextFile(rel_path=rel_path, overwrite=overwrite, _blob_client=blob_client).build()

    def open_binary_file(self, rel_path: str, mode: str | BinaryFileMode) -> BinaryFile:
        self._check_lifecycle_phase()
        # Get and initialize a client for the the blob
        rel_path = self._normalize_rel_path(rel_path)
        mode = self._to_binary_file_mode_enum(mode)
        overwrite = mode == BinaryFileMode.WRITE
        blob_client = self._get_blob_client(rel_path=rel_path)
        # Create a binary file instance
        return AzureBlobBinaryFile(rel_path=rel_path, overwrite=overwrite, _blob_client=blob_client).build()

    def __enter__(self) -> Self:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__enter__()
        self._container_client.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        """Supports 'with' operator for resource initialization and disposal."""
        super(self.__class__, self).__exit__(exc_type, exc_val, exc_tb)
        self._container_client.__exit__(exc_type, exc_val, exc_tb)

    def _get_blob_client(self, *, rel_path: str) -> BlobClient:
        try:
            return self._container_client.get_blob_client(container=self.container_name, blob=rel_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize Azure Blob client.\n"
                f"Container: {self.container_name}\nBlob: {rel_path}\nReason: {exc}"
            ) from exc
