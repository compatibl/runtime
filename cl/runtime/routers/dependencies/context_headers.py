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

from dataclasses import dataclass
from fastapi import Header
from typing_extensions import Annotated


@dataclass(slots=True, kw_only=True)
class ContextHeaders:
    """Class to extract context info from headers."""

    env: str | None
    """Name of the environment (database), e.g. 'Dev;Runtime;V2'"""

    dataset: str | None
    """Dataset string"""

    user: str | None
    """User identifier or identity token"""


def get_context_headers(
    environment: Annotated[str | None, Header(description="Name of the environment (database), e.g. 'Dev;Runtime;V2'")] = None,
    dataset: Annotated[str | None, Header(description="Dataset string")] = None,
    user: Annotated[str | None, Header(description="User identifier or identity token")] = None,
) -> ContextHeaders:
    """Extract information about the context from the headers. Database, dataset and username."""
    return ContextHeaders(env=environment, dataset=dataset, user=user)