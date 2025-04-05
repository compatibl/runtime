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

from enum import IntEnum, auto


class ScriptLanguage(IntEnum):
    """Script language."""

    R = auto()
    """R language."""

    JSON = auto()
    """Json markup."""

    XML = auto()
    """Xml markup."""

    PYTHON = auto()
    """Python language."""

    MARKDOWN = auto()
    """Lightweight markup language."""

    SQL = auto()
    """Sql."""

    CPP = auto()
    """C++ language."""

    C = auto()
    """C language."""

    CSHARP = auto()
    """C# language."""

    JAVA = auto()
    """Java language."""

    TYPESCRIPT = auto()
    """TypeScript language."""

    JAVASCRIPT = auto()
    """JavaScript language."""

    PLAINTEXT = auto()
    """Plaintext."""
