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

from typing_extensions import Self
from cl.runtime.records.record_util import RecordUtil


class InitMixin:
    """Optional mixin class adding init_all(), code must not rely on inheritance from this class."""

    __slots__ = ()
    """To prevent creation of __dict__ in derived types."""

    def init_all(self) -> Self:
        """
        Invoke 'init' for each class in the order from base to derived, then validate against schema.
        Return self to enable method chaining.
        """
        return RecordUtil.init_all(self)
