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
from cl.runtime.routers.dependencies.context_headers import ContextHeaders, get_context_headers
from cl.runtime.routers.storage.dataset_response import DatasetResponseItem
from cl.runtime.routers.storage.datasets_request import DatasetsRequest
from cl.runtime.routers.storage.delete_request import DeleteRequest
from cl.runtime.routers.storage.delete_response_util import DeleteResponseUtil
from cl.runtime.routers.storage.env_response_item import EnvResponseItem
from cl.runtime.routers.storage.save_request import SaveRequest

from cl.runtime.routers.storage.key_request_item import KeyRequestItem
from cl.runtime.routers.storage.load_request import LoadRequest
from cl.runtime.routers.storage.load_response import LoadResponse
from cl.runtime.routers.storage.save_response_util import SaveResponseUtil
from cl.runtime.routers.storage.select_request import SelectRequest
from cl.runtime.routers.storage.select_request_body import SelectRequestBody
from cl.runtime.routers.storage.select_response import SelectResponse

router = APIRouter()


@router.get("/envs", response_model=list[EnvResponseItem])
async def get_envs() -> list[EnvResponseItem]:
    """Information about the environments."""

    return EnvResponseItem.get_envs()


@router.get("/datasets", response_model=list[DatasetResponseItem])
async def get_datasets(
    environment: Annotated[str, Header(None, description="Name of the environment (database).")],
    type_name: Annotated[str, Query(description="Type shortname.")]
) -> list[DatasetResponseItem]:
    """Information about the environments."""

    return DatasetResponseItem.get_datasets(DatasetsRequest(env=environment, type_name=type_name))


@router.post("/load", response_model=LoadResponse)
async def post_load(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    load_keys: Annotated[list[KeyRequestItem] | None, Body(description="List of key objects to load.")] = None,
    ignore_not_found: Annotated[bool, Query(description="If true, empty response will be returned without error if the record is not found.")] = False,
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
    limit: Annotated[int | None, Query(description="Select a specified number of records from the beginning of the list.")] = None,
    skip: Annotated[int, Query(description="Number of skipped records from the beginning of the list.")] = 0,
    table_format: Annotated[bool, Query(description="If true, response will be returned in the table format.")] = True,
) -> SelectResponse:
    """Select records by query."""

    return SelectResponse.get_response(
        SelectRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            type_=select_body.type,
            query_dict=select_body.query_dict,
            limit=limit,
            skip=skip,
            table_format=table_format
        )
    )


@router.post("/delete", response_model=list[KeyRequestItem])
async def delete(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    delete_keys: Annotated[list[KeyRequestItem] | None, Body(description="List of key objects to delete.")] = None
) -> list[KeyRequestItem]:
    """Bulk delete records by list of keys."""

    return DeleteResponseUtil.delete_records(
        DeleteRequest(
            user=context_headers.user,
            env=context_headers.env,
            dataset=context_headers.dataset,
            delete_keys=delete_keys
        )
    )


@router.post("/save", response_model=list[KeyRequestItem])
async def save(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
    records: Annotated[list[dict] | None, Body(description="List of records to save.")] = None,
) -> list[KeyRequestItem]:
    """Save provided records without checking for existence."""

    save_request = SaveRequest(
        user=context_headers.user,
        env=context_headers.env,
        dataset=context_headers.dataset,
        records=records
    )

    save_request = LegacyRequestUtil.format_save_request(save_request)
    return SaveResponseUtil.save_records(save_request)


@router.post("/update")
async def update():
    raise NotImplementedError("/storage/update route is not implemented.")


@router.post("/insert")
async def insert():
    raise NotImplementedError("/storage/insert route is not implemented.")


