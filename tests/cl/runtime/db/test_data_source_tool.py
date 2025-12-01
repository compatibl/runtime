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

import pytest
import io
import json
import zipfile
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.data_source_tool import DataSourceTool
from cl.runtime.db.data_source_tool import _json_serializer
from cl.runtime.file.file_data import FileData
from cl.runtime.file.file_kind import FileKind
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from cl.runtime.tasks.task_status import TaskStatus

@pytest.mark.skip(reason="Skip until storage location issue is resolved")
def test_export(multi_db_fixture):
    """Test export data as zip archive."""

    with active(DataSource) as ds:
        record = ClassMethodTask(
            task_id="2025-11-13-10-14-30-543-7d2199c5d43a985ffb4d",
            type_=ClassMethodTask,
            method_name="stub_method_name",
            queue=TaskQueueKey(queue_id="stub_queue_id"),
            status=TaskStatus.COMPLETED,
        ).build()

        ds.insert_many((record,), commit=True)

        result = DataSourceTool.run_export()
        assert result.name == "_"
        assert result.file_kind == FileKind.ZIP

        buffer = io.BytesIO(result.file_bytes)

        with zipfile.ZipFile(buffer, "r") as zipf:
            path = next(iter(zipf.namelist()))
            file_bytes = zipf.read(path)
            json_data = json.loads(file_bytes.decode("utf-8"))
            deserialized_data = _json_serializer.deserialize(json_data)

            assert deserialized_data == record

@pytest.mark.skip(reason="Skip until storage location issue is resolved")
def test_filter_by_type(multi_db_fixture):
    """Test FilterByQuery class."""
    with active(DataSource) as ds:
        record = ClassMethodTask(
            task_id="2025-11-13-10-14-30-543-7d2199c5d43a985ffb4d",
            type_=ClassMethodTask,
            method_name="stub_method_name",
            queue=TaskQueueKey(queue_id="stub_queue_id"),
            status=TaskStatus.COMPLETED,
        ).build()

        with open("data_source_tool/import.zip", "rb") as zip_file:
            file = zip_file.read()
        DataSourceTool.run_import(FileData(name="_", file_kind=FileKind.ZIP, file_bytes=file))
        result = ds.load_one(record.get_key())
        assert result == record


if __name__ == "__main__":
    pytest.main([__file__])
