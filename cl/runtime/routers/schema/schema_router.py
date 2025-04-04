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
from fastapi import Query
from cl.runtime.routers.schema.type_request import TypeRequest
from cl.runtime.routers.schema.type_response_util import TypeResponseUtil
from cl.runtime.routers.schema.type_successors_response_item import TypeSuccessorsResponseItem
from cl.runtime.routers.schema.types_response_item import TypesResponseItem

router = APIRouter()


@router.get("/types", response_model=list[TypesResponseItem])
async def get_types() -> list[TypesResponseItem]:
    """Information about the record types."""
    return TypesResponseItem.get_types()


@router.get("/type", response_model=dict[str, dict])
async def get_type(
    type_name: Annotated[str, Query(description="Type shortname.")],
) -> dict[str, dict]:
    """Schema for the specified type and its dependencies."""
    return TypeResponseUtil.get_type(TypeRequest(type_name=type_name))


@router.get("/type-successors", response_model=list[TypeSuccessorsResponseItem])
async def get_type_successors(
    type_name: Annotated[str, Query(description="Type shortname.")],
) -> list[TypeSuccessorsResponseItem]:
    """Return type class successors."""
    return TypeSuccessorsResponseItem.get_type_successors(TypeRequest(type_name=type_name))
