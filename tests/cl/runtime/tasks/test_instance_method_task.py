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
import logging.config
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.log.log_config import logging_config
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from stubs.cl.runtime import StubHandlers

TASK_COUNT = 3


def test_smoke(default_db_fixture):
    """Smoke test."""
    records = [
        sample.build()
        for sample in [
            StubHandlers(stub_id="abc"),
        ]
    ]
    active(DataSource).insert_many(records)

    object_and_instance_handler_on_object = [(x, x.run_instance_method_1a) for x in records]
    key_and_instance_handler_on_object = [(x.get_key(), x.run_instance_method_1a) for x in records]
    object_and_instance_handler_on_class = [(x, StubHandlers.run_instance_method_1a) for x in records]
    key_and_instance_handler_on_class = [(x.get_key(), StubHandlers.run_instance_method_1a) for x in records]
    object_and_class_handler_on_class = [(x, StubHandlers.run_class_method_1a) for x in records]
    key_and_class_handler_on_class = [(x.get_key(), StubHandlers.run_class_method_1a) for x in records]

    sample_inputs = (
        object_and_instance_handler_on_object
        + key_and_instance_handler_on_object
        + object_and_instance_handler_on_class
        + key_and_instance_handler_on_class
        + object_and_class_handler_on_class
        + key_and_class_handler_on_class
    )

    for sample_input in sample_inputs:
        key_or_record = sample_input[0]
        method_callable = sample_input[1]
        task = InstanceMethodTask.create(
            queue=TaskQueueKey(queue_id="Sample Queue"),
            key_or_record=key_or_record,
            method_callable=method_callable,
        ).build()
        task.run_task()


def _run_task(task_index: int):
    instance = StubHandlers(stub_id=f"abc{task_index}").build()
    active(DataSource).replace_one(instance)

    task = InstanceMethodTask.create(
        queue=TaskQueueKey(queue_id="Sample Queue"),
        key_or_record=instance,
        method_callable=instance.run_instance_method_1a,
    ).build()

    task.run_task()


def test_task_logger(default_db_fixture, capsys):
    """Test task logger don't share contextual properties."""

    # Set up logging config
    logging.config.dictConfig(logging_config)

    [_run_task(task_index) for task_index in range(TASK_COUNT)]

    # Get stdout lines
    captured_lines = capsys.readouterr().out.splitlines()

    # Check that the stdout lines are not empty and are unique, as they contain specific contextual information
    assert bool(captured_lines)
    assert len(captured_lines) == len(set(captured_lines))


if __name__ == "__main__":
    pytest.main([__file__])
