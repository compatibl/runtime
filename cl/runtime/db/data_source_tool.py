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
import json
import logging
import os
import posixpath
import shutil
import urllib.parse
import zipfile
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.data_source_tool_key import DataSourceToolKey
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.settings.env_settings import EnvSettings
from cl.runtime.settings.project_settings import ProjectSettings
from cl.runtime.storage.local_storage import LocalStorage

_LOGGER = logging.getLogger(__name__)
_json_serializer = DataSerializers.FOR_JSON
_KEY_SERIALIZER = KeySerializers.DELIMITED


@dataclass(slots=True, kw_only=True)
class DataSourceTool(DataSourceToolKey, RecordMixin):
    """Data source tool that allows you to get all your data as zip archive and import new data from zip archive."""

    def get_key(self) -> DataSourceToolKey:
        return DataSourceToolKey(key_id=self.key_id).build()

    @staticmethod
    def run_export() -> FileData:
        """Export tenant data."""
        ds: DataSource = active(DataSource)
        memory_file = io.BytesIO()

        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            base_path = os.path.join(
                ProjectSettings.get_project_root(), ProjectSettings.instance().project_storage, ds.tenant.tenant_id
            )

            for key_type in ds.get_key_types():
                records = ds.load_all(key_type=key_type)

                key_type_name = typename(key_type).removesuffix("Key")
                with LocalStorage(
                    rel_dir=f"{ProjectSettings.instance().project_storage}/{ds.tenant.tenant_id}/{key_type_name}"
                ).build() as storage:
                    for record in records:
                        serialized_data = _json_serializer.serialize(record)
                        file_name = urllib.parse.quote(_KEY_SERIALIZER.serialize(record.get_key()), safe="")
                        storage.save_object(f"{file_name}.json", json.dumps(serialized_data))

            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, base_path)
                    zipf.write(file_path, arc_name)

            shutil.rmtree(base_path)

        memory_file.seek(0)

        date_str = datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
        file_name = f"{date_str}-{EnvSettings.instance().env_id}.zip"

        return FileData(name=file_name, file_kind=FileKind.ZIP, file_bytes=memory_file.getvalue())

    @staticmethod
    def run_import(file: FileData) -> None:
        """Import data for tenant."""
        ds: DataSource = active(DataSource)
        max_workers = min(16, max(2, (os.cpu_count() or 2)))

        MAX_RETRIES = 3

        def _push_batch(records: list[object]) -> int:
            ds.replace_many(records, commit=True)
            return len(records)

        with ThreadPoolExecutor(max_workers=max_workers) as executor, zipfile.ZipFile(
            io.BytesIO(file.file_bytes), "r"
        ) as zipf:
            last_dir = None
            parsed_files = 0
            committed_files = 0
            failed_batches = 0
            retried_batches = 0
            batch: list[object] = []
            pending: list[tuple[Future[None], list[object], int, int]] = []
            BATCH_SIZE = 500

            def submit_batch() -> None:
                nonlocal pending
                if not batch:
                    return
                records = batch[:]
                record_count = len(records)
                batch.clear()
                pending.append((executor.submit(_push_batch, records), records, record_count, 1))
                if len(pending) >= max_workers * 4:
                    reap_completed(False)

            def reap_completed(block: bool) -> None:
                nonlocal pending, committed_files, failed_batches, retried_batches
                still_pending: list[tuple[Future[None], list[object], int, int]] = []
                retry_queue: list[tuple[list[object], int, int]] = []
                for future, records, record_count, attempt in pending:
                    if not block and not future.done():
                        still_pending.append((future, records, record_count, attempt))
                        continue

                    try:
                        future.result()
                        committed_files += record_count
                        _LOGGER.info("Processed %s files so far", committed_files)
                    except Exception as exc:
                        if attempt < MAX_RETRIES:
                            retried_batches += 1
                            _LOGGER.warning(
                                "Batch failed (attempt %s/%s). Retrying.",
                                attempt,
                                MAX_RETRIES,
                            )
                            retry_queue.append((records, record_count, attempt + 1))
                        else:
                            failed_batches += 1
                            _LOGGER.error(
                                "Failed to replace batch asynchronously after %s attempts: %s",
                                attempt,
                                exc,
                            )

                pending = still_pending
                for records, record_count, attempt in retry_queue:
                    pending.append((executor.submit(_push_batch, records), records, record_count, attempt))

            # iterate ZipInfo objects to avoid building separate namelist processing logic
            for info in zipf.infolist():
                path = info.filename

                # skip directory entries (use is_dir if available)
                if (hasattr(info, "is_dir") and info.is_dir()) or path.endswith("/"):
                    continue

                if not path.lower().endswith(".json"):
                    continue

                # use posixpath for ZIP internal paths
                dir_name = posixpath.dirname(path) or "."

                # on folder change flush pending batch (but only clear on successful commit)
                if dir_name != last_dir:
                    submit_batch()
                    reap_completed(False)
                    last_dir = dir_name
                    _LOGGER.info("Starting processing folder: %s", last_dir)

                try:
                    with zipf.open(info) as fh:
                        batch.append(
                            _json_serializer.deserialize(json.loads(fh.read().decode("utf-8")))
                        )
                    parsed_files += 1

                    # commit in batches and log progress when a batch is queued for commit
                    if len(batch) >= BATCH_SIZE:
                        submit_batch()

                except Exception as exc:
                    _LOGGER.error("Failed to process file %s: %s", path, exc)

            submit_batch()
            while pending:
                reap_completed(True)

            _LOGGER.info(
                "Finished processing %s files, committed %s, retries: %s, failed batches: %s",
                parsed_files,
                committed_files,
                retried_batches,
                failed_batches,
            )
