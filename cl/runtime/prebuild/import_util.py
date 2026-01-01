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

import importlib
from types import ModuleType
from typing import Sequence, Callable
from inspect import getmembers
from pkgutil import walk_packages
from memoization import cached


class ImportUtil:
    """Helper methods for working with imports."""

    @classmethod
    @cached
    def get_module(cls, *, module: str) -> ModuleType:
        """Get the module object from the specified module string."""
        try:
            return importlib.import_module(module)
        except:
            raise RuntimeError(f"Import failed for module {module}.")

    @classmethod
    @cached
    def get_modules(cls, *, packages: Sequence[str]) -> tuple[ModuleType, ...]:
        """Get the list of modules in the specified packages."""
        modules = []
        for package in packages:
            # Import root module of the package
            root_module = importlib.import_module(package)
            # Add the root module itself
            modules.append(root_module)
            # Get module info for all submodules, note the trailing period added per walk_packages documentation
            for module_info in walk_packages(root_module.__path__, root_module.__name__ + "."):
                if (module_name := module_info.name).startswith(package):
                    # Import the submodule
                    submodule = importlib.import_module(module_name)
                    modules.append(submodule)
        return tuple(sorted(modules, key=lambda x: x.__name__))

    @classmethod
    @cached
    def get_types(cls, *, packages: Sequence[str], predicate: Callable[[type], bool]) -> tuple[type, ...]:
        """
        Get the list of types in the packages specified in settings.

        Args:
            packages: Packages where search is performed
            predicate: Only the types for which the predicate is true will be returned
        """
        # Enumerate types in all modules that match is_schema_type predicate
        modules = cls.get_modules(packages=packages)
        types = tuple(
            type_
            for module in modules
            for _, type_ in getmembers(module, predicate)
            if module.__name__ == type_.__module__
        )
        return tuple(sorted(types, key=lambda x: x.__name__))