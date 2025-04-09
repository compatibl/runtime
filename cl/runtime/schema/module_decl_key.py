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
from typing import Final
from typing import Type
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.records.for_dataclasses.key import Key

# Temporary global module name, common to all types.
GLOBAL_MODULE_NAME: Final[str] = "cl"


@dataclass(slots=True)
class ModuleDeclKey(Key):
    """Specifies module path in dot-delimited format."""

    module_name: str = required()
    """Module name in dot-delimited format."""

    @classmethod
    def get_key_type(cls) -> Type:
        return ModuleDeclKey

    def __init(self):
        # TODO (Roman): Change the schema so that UI does not have to concatenate the module and type name to get the
        #  key in the schema dict. Sensitive case: drill down polymorphic field when the field value is a derived class,
        #  but in the declaration it is a base class.
        if self.module_name is not None and self.module_name != GLOBAL_MODULE_NAME:
            raise RuntimeError(
                "Using a real module name leads to schema inconsistency for UI. "
                "The module name is temporarily global and should not be specified manually. "
                "Please create ModuleDeclKey without init parameters."
            )

        # Set global module name.
        self.module_name = GLOBAL_MODULE_NAME
