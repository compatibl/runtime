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
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.log_message import LogMessage
from cl.runtime.log.ui_log_util import UiLogUtil
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from cl.runtime.tasks.task_status import TaskStatus
from stubs.cl.runtime import StubDataclass


def test_flat_logs(basic_mongo_db_fixture):
    """Test UiLogUtil.run_get_flat_logs() method."""

    logs_before_clear = [
        LogMessage(message="Info message 1", level="Info").build(),
        LogMessage(message="Info message 2", level="Info").build(),
    ]

    # Save logs before clear marker
    active(DataSource).replace_many(logs_before_clear, commit=True)

    flat_logs = UiLogUtil.run_get_flat_logs()
    assert [x["Message"] for x in flat_logs] == [x.message for x in logs_before_clear]

    # Clear logs
    UiLogUtil.run_clear_logs()

    flat_logs = UiLogUtil.run_get_flat_logs()
    assert flat_logs == []

    # Save logs after clear marker
    logs_after_clear = [
        LogMessage(message="Info message 3", level="Info").build(),
        LogMessage(message="Info message 4", level="Info").build(),
    ]
    active(DataSource).replace_many(logs_after_clear, commit=True)

    flat_logs = UiLogUtil.run_get_flat_logs()
    assert [x["Message"] for x in flat_logs] == [x.message for x in logs_after_clear]


def test_multiple_clear_logs(basic_mongo_db_fixture):
    """Test UiLogUtil.run_clear_logs() multiple calls."""

    logs_before_clear = [
        LogMessage(message="Info message 1", level="Info").build(),
        LogMessage(message="Info message 2", level="Info").build(),
    ]
    active(DataSource).replace_many(logs_before_clear, commit=True)

    flat_logs = UiLogUtil.run_get_flat_logs()
    assert [x["Message"] for x in flat_logs] == [x.message for x in logs_before_clear]

    # Clear logs multiple times
    UiLogUtil.run_clear_logs()
    UiLogUtil.run_clear_logs()
    UiLogUtil.run_clear_logs()
    UiLogUtil.run_clear_logs()

    flat_logs = UiLogUtil.run_get_flat_logs()
    assert flat_logs == []


def test_error_logs(basic_mongo_db_fixture):
    """Test UiLogUtil.run_get_error_logs() method."""

    error_logs_before_clear = [
        LogMessage(message="Error message 2", level="Error").build(),
    ]
    logs_before_clear = [LogMessage(message="Info message 1", level="Info").build(), *error_logs_before_clear]

    # Save info and error logs before clear marker
    active(DataSource).replace_many(logs_before_clear, commit=True)

    error_logs = UiLogUtil.run_get_error_logs()
    assert [x["Message"] for x in error_logs] == [x.message for x in error_logs_before_clear]

    UiLogUtil.run_clear_logs()

    error_logs = UiLogUtil.run_get_error_logs()
    assert error_logs == []

    error_logs_after_clear = [
        LogMessage(message="Error message 4", level="Error").build(),
    ]
    logs_after_clear = [
        LogMessage(message="Info message 3", level="Info").build(),
        *error_logs_after_clear,
    ]

    # Save info and error logs after clear marker
    active(DataSource).replace_many(logs_after_clear, commit=True)

    error_logs = UiLogUtil.run_get_error_logs()
    assert [x["Message"] for x in error_logs] == [x.message for x in error_logs_after_clear]


def test_task_logs(basic_mongo_db_fixture):
    """Test UiLogUtil.run_get_logs_by_task() method."""
    task_1 = ClassMethodTask(
        type_=StubDataclass,
        method_name="stub_method_name",
        queue=TaskQueueKey(queue_id="stub_queue_id"),
        status=TaskStatus.COMPLETED,
    ).build()

    task_1_run_id = task_1.task_id

    active(DataSource).replace_one(task_1, commit=True)

    task_1_logs = [
        LogMessage(message="Task 1. Info message 1.", level="Info", task_run_id=task_1_run_id).build(),
        LogMessage(message="Task 1. Info message 2.", level="Info", task_run_id=task_1_run_id).build(),
    ]

    # Save task logs before clear marker
    active(DataSource).replace_many(task_1_logs, commit=True)

    task_logs = UiLogUtil.run_get_logs_by_task()
    assert len(task_logs) == 1
    assert task_logs[0]["TaskRunId"] == task_1_run_id
    assert [x["Message"] for x in task_logs[0]["Logs"]] == [x.message for x in task_1_logs]

    UiLogUtil.run_clear_logs()
    task_logs = UiLogUtil.run_get_logs_by_task()
    assert task_logs == []

    task_2 = ClassMethodTask(
        type_=StubDataclass,
        method_name="stub_method_name",
        queue=TaskQueueKey(queue_id="stub_queue_id"),
        status=TaskStatus.COMPLETED,
    ).build()

    task_2_run_id = task_2.task_id

    active(DataSource).replace_one(task_2, commit=True)

    task_2_logs = [
        LogMessage(message="Task 2. Info message 1.", level="Info", task_run_id=task_2_run_id).build(),
        LogMessage(message="Task 2. Info message 2.", level="Info", task_run_id=task_2_run_id).build(),
    ]

    # Save task logs after clear marker
    active(DataSource).replace_many(task_2_logs, commit=True)

    task_logs = UiLogUtil.run_get_logs_by_task()
    assert len(task_logs) == 1
    assert task_logs[0]["TaskRunId"] == task_2_run_id
    assert [x["Message"] for x in task_logs[0]["Logs"]] == [x.message for x in task_2_logs]


if __name__ == "__main__":
    pytest.main([__file__])
