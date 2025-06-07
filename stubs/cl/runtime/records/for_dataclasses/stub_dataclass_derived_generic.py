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
from typing import Generic
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic import StubDataclassGeneric, TRecordArg1
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_generic_arg_2 import StubDataclassGenericArg2


@dataclass(slots=True, kw_only=True)
class StubDataclassDerivedGeneric(Generic[TRecordArg1], StubDataclassGeneric[TRecordArg1, StubDataclassGenericArg2]):
    """Stub dataclass-based generic record with one generic parameter replaced by a concrete type."""
