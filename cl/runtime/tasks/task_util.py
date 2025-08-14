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

from cl.runtime import TypeCache
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.tasks.celery.celery_queue import CeleryQueue
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.static_method_task import StaticMethodTask
from cl.runtime.tasks.task import Task

handler_queue = CeleryQueue(queue_id="Handler Queue")


class TaskUtil:
    """Utilities for working with tasks."""

    @classmethod
    def create_tasks_for_submit_request(cls, request: SubmitRequest) -> list[Task]:
        """Create Task objects from task submit request."""

        # TODO: Refactor
        # TODO (Roman): request [None] for static handlers explicitly
        # Workaround for static handlers
        requested_keys = request.keys if request.keys else [None]

        # Add 'run_' prefix to method name to get handler name
        handler_name = f"run_{request.method}"

        # TODO (Roman): Workaround to make handlers with parameters work.
        #  Currently, we do not support non-string arguments for handlers in the MethodTask class model.
        request_arguments = {k: str(v) for k, v in request.arguments.items()} if request.arguments else None
        tasks = []
        for serialized_key in requested_keys:

            # Create handler task
            # TODO: Add request.arguments_ and type_
            if serialized_key is not None:
                # Key is not None, this is an instance method

                if TypeCache.is_type(request.type):
                    # Get key type based on table in request
                    key_type = TypeCache.from_type_name(request.type).get_key_type()  # noqa
                else:
                    # Get key type from table
                    key_type = active(DataSource).get_bound_key_type(table=request.type)

                key_type_str = f"{key_type.__module__}.{TypeUtil.name(key_type)}"
                label = f"{TypeUtil.name(key_type)};{serialized_key};{handler_name}"
                handler_task = InstanceMethodTask(
                    label=label,
                    queue=handler_queue.get_key(),
                    key_type_str=key_type_str,
                    key_str=serialized_key,
                    method_name=handler_name,
                    method_params=request_arguments,
                ).build()
                tasks.append(handler_task)
            else:
                # Key is None, this is a @classmethod or @staticmethod
                record_type = TypeCache.from_type_name(request.type)
                record_type_str = f"{record_type.__module__}.{TypeUtil.name(record_type)}"
                label = f"{TypeUtil.name(record_type)};{handler_name}"
                handler_task = StaticMethodTask(
                    label=label,
                    queue=handler_queue.get_key(),
                    type_str=record_type_str,
                    method_name=handler_name,
                    method_params=request_arguments,
                ).build()
                tasks.append(handler_task)

        return tasks
