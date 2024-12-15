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
from typing import Type

from typing_extensions import Self

from cl.runtime.context.extension_context import ExtensionContext
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class TrialContext(ExtensionContext):
    """Context for a single trial in an experiment."""

    trial: TrialKey = missing()
    """Trial key specified by this context."""
    
    @classmethod
    def get_base_type(cls) -> Type:
        """Return base class of this extension category even if called from a derived class, do not use 'return cls'."""
        return TrialContext

    @classmethod
    def create_default(cls) -> Self:
        """Create default extension instance, this method will be called for the class returned by 'get_base_type'."""
        raise RuntimeError(
            "TrialContext does not have a default, specify using 'with Context(extensions=[TrialContext(...)])'.")
