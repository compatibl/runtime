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

from cl.runtime.serializers.enum_format_enum import EnumFormatEnum
from cl.runtime.serializers.none_format_enum import NoneFormatEnum
from cl.runtime.serializers.enum_serializer import EnumSerializer

cls = EnumSerializer


class EnumSerializers:
    """Standard combinations of primitive formats."""

    PASSTHROUGH: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        enum_format=EnumFormatEnum.PASSTHROUGH,
    ).build()
    """Do not perform any conversion but validate against type information if provided."""

    DEFAULT: cls = cls(
        none_format=NoneFormatEnum.PASSTHROUGH,
        enum_format=EnumFormatEnum.DEFAULT,
    ).build()
    """Serialize as item name string converted to PascalCase."""
