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

from cl.runtime.serializers.data_serializers import DataSerializers
from cl.runtime.serializers.json_format import JsonFormat
from cl.runtime.serializers.json_serializer import JsonSerializer


class JsonSerializers:
    """Standard combinations of primitive formats."""

    DEFAULT = JsonSerializer(
        data_serializer=DataSerializers.FOR_JSON,
    ).build()
    """Include type information as needed, bidirectional, pretty print format."""

    COMPACT = JsonSerializer(
        data_serializer=DataSerializers.FOR_JSON,
        json_output_format=JsonFormat.COMPACT,
    ).build()
    """Include type information as needed, bidirectional, compact format."""

    FOR_REPORTING = JsonSerializer(
        data_serializer=DataSerializers.FOR_JSON_REPORTING,
    ).build()
    """Omit type information when the output is used for reporting, deserialization is not possible."""
