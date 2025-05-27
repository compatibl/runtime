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
from fastapi import Depends
from fastapi import Query
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.routers.entity.panel_response_util import PanelResponseUtil
from cl.runtime.routers.entity.panels_request import PanelsRequest
from cl.runtime.routers.entity.panels_response_item import PanelsResponseItem

router = APIRouter()


@router.get("/panels", response_model=list[PanelsResponseItem])
async def get_panels(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    type_name: Annotated[str, Query(description="Type name")],
    key: Annotated[str | None, Query(description="Primary key fields in semicolon-delimited format")] = None,
) -> list[PanelsResponseItem]:
    """List of panels for the specified record."""
    return PanelsResponseItem.get_response(
        PanelsRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type_name=type_name,
            key=key,
        )
    )


@router.get("/panel", response_model=Any)
async def get_panel(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    type_name: Annotated[str, Query(description="Class name")],
    panel_id: Annotated[str, Query(description="View name")],
    key: Annotated[str | None, Query(description="Primary key fields in semicolon-delimited format")] = None,
) -> Any:
    """Return panel content by its displayed name."""

    return PanelResponseUtil.get_response(
        PanelRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type_name=type_name,
            panel_id=panel_id,
            key=key,
        )
    )
