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
from cl.runtime.records.data_mixin import DataMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.views.script_language import ScriptLanguage


@dataclass(slots=True, kw_only=True)
class Script(DataMixin):
    """Script body element."""

    name: str = required()
    """Script name."""

    language: ScriptLanguage | None = None
    """Script Language."""

    body: list[str] = required()
    """Body"""

    word_wrap: bool | None = None
    """Automatically wrap text to the next line when it reaches the end of a line or a specified margin."""
