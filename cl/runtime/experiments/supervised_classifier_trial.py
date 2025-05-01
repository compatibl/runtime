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
from cl.runtime.experiments.trial import Trial
from cl.runtime.records.for_dataclasses.extensions import required


@dataclass(slots=True, kw_only=True)
class SupervisedClassifierTrial(Trial):
    """Single trial of a supervised classifier experiment, the actual and expected results are string class labels."""

    actual_label: str = required()
    """Actual result of this supervised classifier trial (string class label)."""

    expected_label: str = required()
    """Expected result of this supervised classifier trial (string class label)."""
