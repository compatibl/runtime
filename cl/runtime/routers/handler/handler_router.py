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
from typing import Any
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.routers.handler.run_response_item import RunResponseItem
from cl.runtime.routers.tasks.submit_request import SubmitRequest
from cl.runtime.routers.tasks.submit_request_body import SubmitRequestBody

router = APIRouter()


@router.post("/run", response_model=Any)
async def post_run(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    submit_body: Annotated[SubmitRequestBody, Body(description="Submit request body.")],
) -> Any:
    """Run handler in main process."""

    return RunResponseItem.get_response(
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
