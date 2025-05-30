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

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.protocols import TKey
from cl.runtime.records.record_mixin import RecordMixin

TExperimentKey = TypeVar("TExperimentKey")


class TrialMixin(Generic[TKey, TExperimentKey], RecordMixin[TKey], ABC):
    """Result and supporting data for a trial of an experiment."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @property
    @abstractmethod
    def timestamp(self) -> str:
        """Unique trial timestamp."""

    @timestamp.setter
    @abstractmethod
    def timestamp(self, value: str) -> None:
        """Unique trial timestamp."""
        pass

    @property
    @abstractmethod
    def experiment(self) -> TExperimentKey:
        """Experiment for which the trial is recorded."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""
        # Create a unique timestamp
        if self.timestamp is None:
            self.timestamp = Timestamp.create()
