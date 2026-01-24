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
from cl.runtime.tasks.class_method_task import ClassMethodTask
from cl.runtime.tasks.task_queue_key import TaskQueueKey
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers import StubHandlers


def test_create(default_db_fixture, event_broker_fixture):
    """Test 'test_create' method."""
    sample_inputs = [
        (StubHandlers, StubHandlers.run_class_method_1a),
        (StubHandlers, StubHandlers.run_static_method_1a),
    ]

    for sample_input in sample_inputs:
        record_type = sample_input[0]
        method_callable = sample_input[1]
        task = ClassMethodTask.create(
            queue=TaskQueueKey(queue_id="Sample Queue"), record_type=record_type, method_callable=method_callable
        ).build()
        task.run_task()


if __name__ == "__main__":
    pytest.main([__file__])
