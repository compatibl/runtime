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

from typing import TYPE_CHECKING, Optional

from cl.runtime.storage.data_set_util import DataSetUtil

if TYPE_CHECKING:
    from cl.runtime.storage.data_source import DataSource


class Context:
    """
    Context provides:

    * Default data source
    * Default dataset of the default data source
    * Logging
    * Progress reporting
    * Filesystem access (if available)
    """

    __slots__ = ('__data_source', '__data_set',)

    __data_source: Optional['DataSource']
    __data_set: Optional[str]

    def __init__(self):
        """
        Set instant variables to None here. They will be
        set and then initialized by the respective
        property setter.
        """

        self.__data_source = None
        """Default data source of the context."""

        self.__data_set = None
        """Default dataset of the context."""

    @property
    def data_source(self) -> 'DataSource':
        """Return data_source property, error message if not set."""

        if not self.__data_source:
            raise Exception('Data source property is not set in Context.')
        return self.__data_source

    @data_source.setter
    def data_source(self, value: 'DataSource') -> None:
        """Set data_source property and pass self to its init method."""
        self.__data_source = value

    @property
    def data_set(self) -> str:
        """Return data_set property, error message if not set."""

        if self.__data_set is None:
            raise Exception('Dataset property is not set in Context.')
        return self.__data_set

    @data_set.setter
    def data_set(self, value: str) -> None:
        """Set data_set property."""

        if self.__data_set is not None:
            raise ValueError('The data_set field in context is immutable, create a new context instead.')

        # Import inside method to avoid cyclic reference
        from cl.runtime.storage.data_set_util import DataSetUtil

        # Perform validation by converting into tokens, discard the result
        DataSetUtil.to_tokens(value)

        self.__data_set = value

    def __enter__(self):
        """Supports with syntax for resource disposal."""

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Supports with syntax for resource disposal."""

        if self.__data_source is not None:
            self.__data_source.__exit__(exc_type, exc_val, exc_tb)

        # Return False to propagate exception to the caller
        return False

