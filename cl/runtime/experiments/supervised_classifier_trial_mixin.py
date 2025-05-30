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
from typing import Generic
from cl.runtime.experiments.classifier_trial_mixin import ClassifierTrialMixin
from cl.runtime.experiments.trial_mixin import TExperimentKey
from cl.runtime.records.protocols import TKey


class SupervisedClassifierTrialMixin(Generic[TKey, TExperimentKey], ClassifierTrialMixin[TKey, TExperimentKey], ABC):
    """Single trial of a supervised experiment where each trial has True or False outcome."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    @property
    @abstractmethod
    def expected(self) -> str:
        """Expected result of the trial (class label)."""
