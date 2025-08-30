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

from frozendict import frozendict

from stubs.cl.runtime.records.for_dataclasses.stub_dataclass import StubDataclass


@dataclass(slots=True, kw_only=True)
class StubDataclassEmptyFields(StubDataclass):
    """Stub dataclass with empty fields."""

    empty_str: str | None = None
    """Empty string field."""

    empty_list: list[str] | None = None
    """Empty list field."""

    empty_tuple: tuple[str, ...] | None = None
    """Empty tuple field."""

    empty_dict: dict[str, str] | None = None
    """Empty dict field."""

    empty_frozendict: frozendict[str, str] | None = None
    """Empty frozendict field."""
