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

from __future__ import annotations
from abc import ABC
from typing_extensions import Self
from cl.runtime.data.data import Data


class Key(Data, ABC):
    """
    Optional mixin class for database record keys.

    The use of this class is optional. The code must not rely on inheritance from this class, but only on the
    presence of its methods. These methods may be implemented without using any specific base or mixin class.

    The methods that lack implementation must be overridden by a derived class in code or using a decorator.
    They are not made abstract to avoid errors from static type checkers in the latter case.
    """

    def get_table(self) -> str:
        """
        Name of the database table where the record for this key is stored.

        By convention, table name consists of a namespace (full package path or short alias)
        followed by the dot delimiter and then the class name of the common base to all records
        stored in the table: 'namespace.RecordType'
        """
        raise RuntimeError(f"Method get_table() for class {type(self).__name__} in module {type(self).__module__} "
                           f"is neither implemented in code nor by a decorator.")

    def get_key(self) -> str:
        """
        Key as string in semicolon-delimited string format without table name. 
        
        For composite keys, the embedded keys are concatenated in the order of their declaration without brackets:

            - No primary key fields: '' (i.e. empty string)
            - One primary key field A: 'A'
            - Two primary key fields A and B: 'A;B'
            - Two primary key fields 'A1;A2' and 'B': 'A1;A2;B'
        """
        raise RuntimeError(f"Method get_key() for class {type(self).__name__} in module {type(self).__module__} "
                           f"is neither implemented in code nor by a decorator.")

    def to_key(self) -> Self:
        """Return deep copy of the key base class when invoked for a derived record class."""
        raise RuntimeError(f"Method to_key() for class {type(self).__name__} in module {type(self).__module__} "
                           f"is neither implemented in code nor by a decorator.")

    def get_generic_key(self) -> str:
        """
        Generic key string defines both the table and the record within the table. It consists of the
        table name followed by the primary key in semicolon-delimited string format.

        By convention, table name consists of a namespace (full package path or short alias) followed by
        the class name of the common base to all classes stored in the table with dot delimiter:

        - No primary key fields: 'namespace.RecordType'
        - One primary key field A: 'namespace.RecordType;A'
        - Two primary key fields A and B: 'namespace.RecordType;A;B'
        - Two primary key fields 'A1;A2' and 'B': 'namespace.RecordType;A1;A2;B'
        """
        return f"{self.get_table()};{self.get_key()}"

    def __str__(self) -> str:
        """
        Key as string in semicolon-delimited string format without table name.

        This method is for debugging purposes only and may be overridden to return additional data.
        Data source implementation must use get_key() method instead.
        """
        return self.get_key()
