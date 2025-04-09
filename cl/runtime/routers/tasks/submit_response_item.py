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

from __future__ import annotations
from pydantic import BaseModel
from cl.runtime import TypeImport
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.contexts.log_context import LogContext
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.tasks.celery.celery_queue import CeleryQueue
from cl.runtime.tasks.instance_method_task import InstanceMethodTask
from cl.runtime.tasks.static_method_task import StaticMethodTask

handler_queue = CeleryQueue(queue_id="Handler Queue")


class SubmitResponseItem(BaseModel):
    """Response data type for the /tasks/submit route."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    task_run_id: str
    """Task run identifier."""

    key: str | None
    """Key string in semicolon-delimited format."""

    @classmethod
    def get_response(cls, request: SubmitRequest) -> list[SubmitResponseItem]:
        """Submit tasks and return list of task response items."""

        response_items = []

        # TODO: Refactor
        # TODO (Roman): request [None] for static handlers explicitly
        # Workaround for static handlers
        requested_keys = request.keys if request.keys else [None]

        # Run task for all keys in request
        for serialized_key in requested_keys:

            with LogContext(type=request.type, handler=request.method).build():
                # Create handler task
                # TODO: Add request.arguments_ and type_
                if serialized_key is not None:
                    # Key is not None, this is an instance method

                    # Get key type based on table in request
                    key_type = TypeImport.get_class_from_type_name(request.type).get_key_type()  # noqa

                    key_type_str = f"{key_type.__module__}.{TypeUtil.name(key_type)}"
                    method_name_pascal_case = CaseUtil.snake_to_pascal_case(request.method)
                    label = f"{TypeUtil.name(key_type)};{serialized_key};{method_name_pascal_case}"
                    handler_task = InstanceMethodTask(
                        label=label,
                        queue=handler_queue.get_key(),
                        key_type_str=key_type_str,
                        key_str=serialized_key,
                        method_name=request.method,
                        method_params=request.arguments,
                    ).build()
                else:
                    # Key is None, this is a @classmethod or @staticmethod
                    record_type = TypeImport.get_class_from_type_name(request.type)
                    record_type_str = f"{record_type.__module__}.{TypeUtil.name(record_type)}"
                    method_name_pascal_case = CaseUtil.snake_to_pascal_case(request.method)
                    label = f"{TypeUtil.name(record_type)};{method_name_pascal_case}"
                    handler_task = StaticMethodTask(
                        label=label,
                        queue=handler_queue.get_key(),
                        type_str=record_type_str,
                        method_name=request.method,
                        method_params=request.arguments,
                    ).build()

                # Save and submit task
                DbContext.save_one(handler_task)
                handler_queue.submit_task(handler_task)  # TODO: Rely on query instead
                response_items.append(SubmitResponseItem(key=serialized_key, task_run_id=handler_task.task_id))

        return response_items
