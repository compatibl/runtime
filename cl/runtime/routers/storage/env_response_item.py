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

from __future__ import annotations
from pydantic import BaseModel
from cl.runtime.contexts.context_manager import active
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.server.env import Env


class EnvResponseItem(BaseModel):
    """Response data type for the /storage/envs route."""

    name: str
    """Name of the environment."""

    parent: str | None = None
    """Name of the parent environment."""

    class Config:
        alias_generator = CaseUtil.snake_to_pascal_case
        populate_by_name = True

    @classmethod
    def get_envs(cls) -> list[EnvResponseItem]:
        """Implements /storage/get_envs route."""

        # Default response when running locally without authorization
        result_dict = {
            "Name": active(Env).env_id,
            "Parent": "",  # TODO: Check if None is also accepted
        }

        return [EnvResponseItem(**result_dict)]
