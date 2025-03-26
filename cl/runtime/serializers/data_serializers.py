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

from cl.runtime.serializers.data_serializer import DataSerializer
from cl.runtime.serializers.enum_serializers import EnumSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.serializers.primitive_serializers import PrimitiveSerializers
from cl.runtime.serializers.type_format_enum import TypeFormatEnum
from cl.runtime.serializers.type_inclusion_enum import TypeInclusionEnum

cls = DataSerializer


class DataSerializers:
    """Standard combinations of primitive formats."""

    PASSTHROUGH: cls = cls(
        type_inclusion=TypeInclusionEnum.AS_NEEDED,
        type_format=TypeFormatEnum.NAME_ONLY,
        primitive_serializer=PrimitiveSerializers.PASSTHROUGH,
        enum_serializer=EnumSerializers.PASSTHROUGH,
    ).build()
    """Bidirectional conversion of classes to dicts and back without any conversion of primitive types or enums."""

    DEFAULT: cls = cls(
        type_inclusion=TypeInclusionEnum.AS_NEEDED,
        type_format=TypeFormatEnum.NAME_ONLY,
        primitive_serializer=PrimitiveSerializers.DEFAULT,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()
    """Default bidirectional data serializer with default serialization for primitive types and enums."""

    FOR_JSON: cls = cls(
        type_inclusion=TypeInclusionEnum.AS_NEEDED,
        type_format=TypeFormatEnum.NAME_ONLY,
        primitive_serializer=PrimitiveSerializers.FOR_JSON,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()
    """Default bidirectional data serializer settings for JSON."""

    FOR_UI: cls = cls(
        type_inclusion=TypeInclusionEnum.ALWAYS,
        type_format=TypeFormatEnum.NAME_ONLY,
        type_field="_t",
        pascalize_keys=True,
        primitive_serializer=PrimitiveSerializers.DEFAULT,
        enum_serializer=EnumSerializers.DEFAULT,
        key_serializer=KeySerializers.DELIMITED,
    ).build()
    """Default bidirectional data serializer settings for UI."""

    FOR_MONGO: cls = cls(
        type_inclusion=TypeInclusionEnum.AS_NEEDED,
        type_format=TypeFormatEnum.NAME_ONLY,
        primitive_serializer=PrimitiveSerializers.FOR_MONGO,
        enum_serializer=EnumSerializers.DEFAULT,
    ).build()
    """Default bidirectional data serializer settings for MongoDB."""
