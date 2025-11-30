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

from typing import Annotated
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.routers.tasks.cancel_request import CancelRequest
from cl.runtime.routers.tasks.cancel_response_item import CancelResponseItem
from cl.runtime.routers.tasks.result_request import ResultRequest
from cl.runtime.routers.tasks.result_response_item import ResultResponseItem
from cl.runtime.routers.tasks.status_request import StatusRequest
from cl.runtime.routers.tasks.status_response_item import StatusResponseItem
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.routers.tasks.submit_request_body import SubmitRequestBody
from cl.runtime.routers.tasks.submit_response_item import SubmitResponseItem
from cl.runtime.routers.tasks.task_run_ids_request_body import TaskRunIdsRequestBody

router = APIRouter()


@router.post("/submit", response_model=list[SubmitResponseItem])
async def post_submit(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    submit_body: Annotated[SubmitRequestBody, Body(description="Submit request body.")],
) -> list[SubmitResponseItem]:
    """Submit run handler in Celery task."""

    return SubmitResponseItem.get_response(
        SubmitRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type=submit_body.type,
            method=submit_body.method,
            keys=submit_body.keys,
            arguments=submit_body.arguments,
            user_keys=context_headers.user_keys,
        )
    )


@router.post("/cancel", response_model=list[CancelResponseItem])
async def post_cancel(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to cancel.")],
) -> list[CancelResponseItem]:
    """Cancel tasks by run ids."""

    return CancelResponseItem.get_response(
        CancelRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            task_run_ids=task_run_ids.task_run_ids,
        )
    )


@router.post("/cancel_all", response_model=list[CancelResponseItem])
async def post_cancel_all(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
) -> list[CancelResponseItem]:
    """Cancel all running tasks."""

    return CancelResponseItem.get_response(
        CancelRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            task_run_ids=[],  # Empty list for cancel_all
            cancel_all=True,
        )
    )


@router.post("/status", response_model=list[StatusResponseItem])
async def post_status(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to get status.")],
) -> list[StatusResponseItem]:
    """Bulk request task statuses by run ids."""

    return StatusResponseItem.get_response(
        StatusRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            task_run_ids=task_run_ids.task_run_ids,
        )
    )


@router.post("/result", response_model=list[ResultResponseItem])
async def post_result(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    task_run_ids: Annotated[TaskRunIdsRequestBody, Body(description="Task run ids to get result.")],
) -> list[ResultResponseItem]:
    """Bulk request task results by run ids."""

    return ResultResponseItem.get_response(
        ResultRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            task_run_ids=task_run_ids.task_run_ids,
        )
    )
