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

from cl.runtime.records.protocols import TData
from cl.runtime.serializers.slots_util import SlotsUtil


class CloneUtil:
    """Helper class for cloning."""

    @classmethod
    def clone(cls, obj: TData) -> TData:
        """Return an unfrozen object of the same type populated by shallow copies of public fields."""
        return cls.clone_as(obj, type(obj))

    @classmethod
    def clone_as(cls, obj: TData, result_type: type[TData]) -> TData:
        """Return an unfrozen object of the specified type populated by shallow copies of public fields."""
        result = result_type()  # TODO: Consider using constructor with fields
        slots = SlotsUtil.get_slots(type(obj))
        for attr in slots:
            if not attr.startswith("_"):  # Skip private fields
                setattr(result, attr, getattr(obj, attr))
        return result
