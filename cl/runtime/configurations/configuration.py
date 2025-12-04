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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from cl.runtime.configurations.configuration_key import ConfigurationKey
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.record_mixin import RecordMixin


@dataclass(slots=True, kw_only=True)
class Configuration(ConfigurationKey, RecordMixin, ABC):
    """Performs configuration when run_configure is invoked."""

    autorun: bool | None = None
    """Set this flag to invoke run_configure automatically after preloads are completed."""

    def get_key(self) -> ConfigurationKey:
        return ConfigurationKey(configuration_id=self.configuration_id).build()

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Use globally unique UUIDv7-based timestamp if not specified
        if self.configuration_id is None:
            self.configuration_id = Timestamp.create()

    @abstractmethod
    def run_configure(self) -> None:
        """Perform configuration."""
