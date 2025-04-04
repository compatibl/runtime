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
from fastapi import Header
from fastapi import Query
from cl.runtime.legacy.legacy_request_util import LegacyRequestUtil
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.routers.storage.datasets_request import DatasetsRequest
from cl.runtime.routers.storage.datasets_response_item import DatasetsResponseItem
from cl.runtime.routers.storage.delete_request import DeleteRequest
from cl.runtime.routers.storage.delete_response_util import DeleteResponseUtil
from cl.runtime.routers.storage.env_response_item import EnvResponseItem
from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.load_response import LoadResponse
from cl.runtime.routers.storage.save_request import SaveRequest
from cl.runtime.routers.storage.save_response_util import SaveResponseUtil
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.routers.storage.select_request_body import SelectRequestBody
from cl.runtime.routers.storage.select_response import SelectResponse
from cl.runtime.routers.storage.update_request_item import UpdateRequestItem

router = APIRouter()


@router.get("/envs", response_model=list[EnvResponseItem])
async def get_envs() -> list[EnvResponseItem]:
    """Information about the environments."""

    return EnvResponseItem.get_envs()


@router.get("/datasets", response_model=list[DatasetsResponseItem])
async def get_datasets(
    type_name: Annotated[str, Query(description="Type shortname.")],
    environment: Annotated[str, Header(description="Name of the environment (database).")] = None,
) -> list[DatasetsResponseItem]:
    """Information about the environments."""
    return DatasetsResponseItem.get_datasets(DatasetsRequest(env=environment, type_name=type_name))


@router.post("/load", response_model=LoadResponse)
async def post_load(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    load_keys: Annotated[list[KeyRequestItem] | None, Body(description="List of key objects to load.")] = None,
    ignore_not_found: Annotated[
        bool, Query(description="If true, empty response will be returned without error if the record is not found.")
    ] = False,
) -> LoadResponse:
    """Bulk load records by list of keys."""

    return LoadResponse.get_response(
        LoadRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            load_keys=load_keys,
            ignore_not_found=ignore_not_found,
        )
    )


@router.post("/select", response_model=SelectResponse)
async def post_select(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    select_body: Annotated[SelectRequestBody, Body(description="Select request body.")],
    limit: Annotated[
        int | None, Query(description="Select a specified number of records from the beginning of the list.")
    ] = None,
    skip: Annotated[int, Query(description="Number of skipped records from the beginning of the list.")] = 0,
    table_format: Annotated[bool, Query(description="If true, response will be returned in the table format.")] = True,
) -> SelectResponse:
    """Select records by query."""

    # TODO (Roman): Support select with 'limit'.
    limit = None

    return SelectResponse.get_response(
        SelectRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type_=select_body.type,
            query_dict=select_body.query_dict,
            limit=limit,
            skip=skip,
            table_format=table_format,
        )
    )


@router.post("/delete", response_model=list[KeyRequestItem])
async def post_delete(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    delete_keys: Annotated[list[KeyRequestItem] | None, Body(description="List of key objects to delete.")] = None,
) -> list[KeyRequestItem]:
    """Bulk delete records by list of keys."""

    return DeleteResponseUtil.delete_records(
        DeleteRequest(
            user=context_headers.user, env=context_headers.env, dataset=context_headers.dataset, delete_keys=delete_keys
        )
    )


@router.post("/save", response_model=list[KeyRequestItem])
async def post_save(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    records: Annotated[list[dict] | None, Body(description="List of records to save.")] = None,
) -> list[KeyRequestItem]:
    """Bulk save records to DB. Don't check if the record already exists."""

    save_request = SaveRequest(
        user=context_headers.user, env=context_headers.env, dataset=context_headers.dataset, records=records
    )

    save_request = LegacyRequestUtil.format_save_request(save_request)
    return SaveResponseUtil.save_records(save_request)


@router.post("/update", response_model=list[KeyRequestItem])
async def post_update(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],  # noqa unused
    update_items: Annotated[
        list[UpdateRequestItem] | None, Body(description="List of update items.")
    ] = None,  # noqa unused
) -> list[KeyRequestItem]:
    """
    Bulk update records in DB. Single update item represents key and new record for this key.

    If updated record has the same key - update this record.
    Else - try to save new record without deleting old one, fails if updated record already exists.
    """
    # TODO (Roman): Implement /update route.
    raise NotImplementedError("/storage/update route is not implemented.")


@router.post("/insert", response_model=list[KeyRequestItem])
async def post_insert(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],  # noqa unused
    records: Annotated[list[dict] | None, Body(description="List of records to insert.")] = None,  # noqa unused
) -> list[KeyRequestItem]:
    """Bulk insert records to DB. The same as /storage/save route but fails if the record already exists."""
    # TODO (Roman): Implement /insert route.
    raise NotImplementedError("/storage/insert route is not implemented.")
