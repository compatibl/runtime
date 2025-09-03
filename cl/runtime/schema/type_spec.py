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
from dataclasses import dataclass
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.protocols import is_data_key_or_record_type
from cl.runtime.records.protocols import is_enum_type
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_primitive_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.type_kind import TypeKind


@dataclass(slots=True, kw_only=True)
class TypeSpec(BootstrapMixin, ABC):
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    type_: type
    """Class where the type is stored (this is not the type hint as it excludes container and optional info)."""

    type_kind: TypeKind = required()
    """Type kind (primitive, enum, data, key, record), initialized from _class if not set."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Set type kind
        if is_primitive_type(self.type_):
            self.type_kind = TypeKind.PRIMITIVE
        elif is_enum_type(self.type_):
            self.type_kind = TypeKind.ENUM
        elif is_key_type(self.type_):
            self.type_kind = TypeKind.KEY
        elif is_record_type(self.type_):
            self.type_kind = TypeKind.RECORD
        elif is_data_key_or_record_type(self.type_):
            self.type_kind = TypeKind.DATA
        else:
            # This should not happen because this method is only invoked for data types, but just in case
            raise RuntimeError(
                f"Dataclass {typename(self.type_)} is neither a primitive type, enum, key, record or data."
            )
