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

import datetime as dt
from uuid import UUID
from cl.runtime.schema.type_hint import TypeHint


class TypeHints:
    """Standard type hints."""

    STR_OR_NONE: TypeHint = TypeHint.for_type(str, optional=True)
    """Type hint for str | None."""

    FLOAT_OR_NONE: TypeHint = TypeHint.for_type(float, optional=True)
    """Type hint for float | None."""

    BOOL_OR_NONE: TypeHint = TypeHint.for_type(bool, optional=True)
    """Type hint for bool | None."""

    INT_OR_NONE: TypeHint = TypeHint.for_type(int, optional=True)
    """Type hint for int | None."""

    DATE_OR_NONE: TypeHint = TypeHint.for_type(dt.date, optional=True)
    """Type hint for date | None."""

    TIME_OR_NONE: TypeHint = TypeHint.for_type(dt.time, optional=True)
    """Type hint for time | None."""

    DATETIME_OR_NONE: TypeHint = TypeHint.for_type(dt.datetime, optional=True)
    """Type hint for datetime | None."""

    UUID_OR_NONE: TypeHint = TypeHint.for_type(UUID, optional=True)
    """Type hint for UUID | None."""

    BYTES_OR_NONE: TypeHint = TypeHint.for_type(bytes, optional=True)
    """Type hint for bytes | None."""
