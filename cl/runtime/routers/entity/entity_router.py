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

from typing import Dict
from typing import List
from fastapi import APIRouter
from fastapi import Body
from fastapi import Header
from fastapi import Query
from cl.runtime.legacy.legacy_response_util import LegacyResponseUtil
from cl.runtime.routers.entity.delete_request import DeleteRequest
from cl.runtime.routers.entity.delete_response import DeleteResponse
from cl.runtime.routers.entity.list_panels_request import ListPanelsRequest
from cl.runtime.routers.entity.list_panels_response_item import ListPanelsResponseItem
from cl.runtime.routers.entity.panel_request import PanelRequest
from cl.runtime.routers.entity.panel_response_util import PanelResponse
from cl.runtime.routers.entity.panel_response_util import PanelResponseUtil
from cl.runtime.routers.entity.save_request import SaveRequest
from cl.runtime.routers.entity.save_response import SaveResponse

router = APIRouter()


# TODO: Consider changing to /panels for consistency
@router.get("/list_panels", response_model=List[ListPanelsResponseItem])
async def get_list_panels(
    type: str = Query(..., description="Class name"),  # noqa Suppress report about shadowed built-in type
    key: str = Query(None, description="Primary key fields in semicolon-delimited format"),
    dataset: str = Query(None, description="Dataset string"),
    user: str = Header(None, description="User identifier or identity token"),
) -> List[ListPanelsResponseItem]:
    """List of panels for the specified record."""
    return ListPanelsResponseItem.get_response(ListPanelsRequest(type=type, key=key, dataset=dataset, user=user))


@router.get("/panel", response_model=PanelResponse)
async def get_panel(
    type: str = Query(..., description="Class name"),  # noqa Suppress report about shadowed built-in type
    panel_id: str = Query(..., description="View name"),
    key: str = Query(None, description="Primary key fields in semicolon-delimited format"),
    dataset: str = Query(None, description="Dataset string"),
) -> PanelResponse:
    """Return panel content by its displayed name."""
    response = PanelResponseUtil.get_response(PanelRequest(type=type, panel_id=panel_id, key=key, dataset=dataset))
    return LegacyResponseUtil.format_panel_response(response)


@router.post("/save", response_model=SaveResponse)
async def save(
    record_in_dict: Dict = Body(..., description="Dict representation of the record to be saved/updated."),
    old_record_key: str = Query(None, description="Optional key of the record to be updated"),
    dataset: str = Query(None, description="Dataset string"),
    user: str = Header(None, description="User identifier or identity token"),
) -> SaveResponse:
    """Save panel content."""
    return SaveResponse.get_response(
        SaveRequest(
            record_dict=record_in_dict,
            old_record_key=old_record_key,
            dataset=dataset,
            user=user,
        ),
    )


@router.post("/delete_many", response_model=DeleteResponse)
async def delete_many(
    record_keys: List[Dict] = Body(..., description="The list of keys to delete."),
    dataset: str = Query(None, description="Dataset string"),
    user: str = Header(None, description="User identifier or identity token"),
) -> DeleteResponse:
    """Delete entities."""

    return DeleteResponse.get_response(
        DeleteRequest(
            record_keys=record_keys,  # noqa
            dataset=dataset,
            user=user,
        ),
    )
