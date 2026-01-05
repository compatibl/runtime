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

from typing import Annotated, Any
from fastapi import APIRouter
from fastapi import Body

from cl.runtime.routers.task.cancel_request import CancelRequest
from cl.runtime.routers.task.cancel_response_item import CancelResponseItem
from cl.runtime.routers.task.result_request import ResultRequest
from cl.runtime.routers.task.result_response_item import ResultResponseItem
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_request_body import RunRequestBody
from cl.runtime.routers.task.run_response_util import RunResponseUtil
from cl.runtime.routers.task.status_request import StatusRequest
from cl.runtime.routers.task.status_response_item import StatusResponseItem
from cl.runtime.routers.task.submit_request import SubmitRequest
from cl.runtime.routers.task.submit_request_body import SubmitRequestBody
from cl.runtime.routers.task.submit_response_item import SubmitResponseItem
from cl.runtime.routers.task.task_run_ids_request_body import TaskRunIdsRequestBody

router = APIRouter()


@router.post("/run", response_model=Any)
async def post_run(
    run_body: Annotated[RunRequestBody, Body(description="Run request body.")],
) -> Any:
    """Route to run Task and return result in Response."""

    return RunResponseUtil.get_response(
        RunRequest(
            type=run_body.type,
            method=run_body.method,
            key=run_body.key,
            arguments=run_body.arguments,
        )
    )


@router.post("/submit", response_model=list[SubmitResponseItem])
async def post_submit(
    submit_body: Annotated[SubmitRequestBody, Body(description="Submit request body.")],
) -> list[SubmitResponseItem]:
    """Route to bulk submit Tasks and return task_run_id's in Response."""

    return SubmitResponseItem.get_response(
        SubmitRequest(
            type=submit_body.type,
            method=submit_body.method,
            keys=submit_body.keys,
            arguments=submit_body.arguments,
        )
    )

@router.post("/cancel", response_model=list[CancelResponseItem])
async def post_cancel(
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to cancel.")],
) -> list[CancelResponseItem]:
    """Cancel tasks by run ids."""

    return CancelResponseItem.get_response(
        CancelRequest(
            task_run_ids=task_run_ids.task_run_ids,
        )
    )


@router.post("/cancel_all", response_model=list[CancelResponseItem])
async def post_cancel_all() -> list[CancelResponseItem]:
    """Cancel all running tasks."""

    return CancelResponseItem.get_response(
        CancelRequest(
            task_run_ids=[],  # Empty list for cancel_all
            cancel_all=True,
        )
    )


@router.post("/status", response_model=list[StatusResponseItem])
async def post_status(
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to get status.")],
) -> list[StatusResponseItem]:
    """Bulk request task statuses by run ids."""

    return StatusResponseItem.get_response(
        StatusRequest(
            task_run_ids=task_run_ids.task_run_ids,
        )
    )


@router.post("/result", response_model=list[ResultResponseItem])
async def post_result(
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to get result.")],
) -> list[ResultResponseItem]:
    """Bulk request task results by run ids."""

    return ResultResponseItem.get_response(
        ResultRequest(
            task_run_ids=task_run_ids.task_run_ids,
        )
    )
