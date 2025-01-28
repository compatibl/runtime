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

from typing import Any


class FreezableUtil:
    """Helper methods for any implementation of Freezable, not specific to dataclasses."""

    @classmethod
    def is_frozen(cls, possibly_freezable: Any):
        """
        Call 'is_frozen' method if implemented, return False if not (even if the dataclass attribute 'frozen' is set).
        This method does not rely on inheritance from Freezable and is not specific to dataclasses.
        """
        if (is_frozen_callable := getattr(possibly_freezable, "is_frozen", None)) is not None:
            return is_frozen_callable()
        else:
            return False

    @classmethod
    def try_freeze(cls, possibly_freezable: Any) -> bool:
        """
        Call freeze method and return True if implemented, exit without error and return False if not.
        This method does not rely on inheritance from any version of Freezable and is not specific to dataclasses.
        """
        if (freeze_callable := getattr(possibly_freezable, "freeze", None)) is not None:
            freeze_callable()
            return True
        else:
            return False
