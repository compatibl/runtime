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
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_request_body import RunRequestBody
from cl.runtime.routers.task.run_response_util import RunResponseUtil
from cl.runtime.routers.task.submit_request import SubmitRequest
from cl.runtime.routers.task.submit_request_body import SubmitRequestBody
from cl.runtime.routers.task.submit_response_item import SubmitResponseItem

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
            keys=submit_body.key,
            arguments=submit_body.arguments,
        )
    )
