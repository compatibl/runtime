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
from fastapi import Depends
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.routers.task.run_request import RunRequest
from cl.runtime.routers.task.run_request_body import RunRequestBody
from cl.runtime.routers.task.run_response_util import RunResponseUtil

router = APIRouter()


@router.post("/run", response_model=Any)
async def post_run(
    # TODO (Roman): Review context_headers
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    run_body: Annotated[RunRequestBody, Body(description="Run request body.")],
) -> Any:
    """Run Celery task."""

    return RunResponseUtil.get_response(
        RunRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type=run_body.type,
            method=run_body.method,
            key=run_body.key,
            arguments=run_body.arguments,
        )
    )

