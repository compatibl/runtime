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

from typing import Optional, final

from cl.runtime.view.binary_content_key import BinaryContentKey
from cl.runtime.view.binary_content_type_enum import BinaryContentTypeEnum
from cl.runtime.primitive.variant import Variant
from cl.runtime.storage.attrs import data_class, data_field


@final
@data_class
class BinaryContent(BinaryContentKey):
    """Display the specified embedded binary content."""

    name: Optional[Variant] = data_field()
    """Content name."""

    content: bytes = data_field()
    """Embedded binary content to be displayed as the current view."""

    content_type: BinaryContentTypeEnum = data_field()
    """Embedded binary content type."""