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
import pkgutil
from types import ModuleType
from typing import Sequence, Callable
from inspect import getmembers
from pkgutil import walk_packages

class ImportUtil:
    """Helper methods for working with imports."""

    @classmethod
    def check_imports(cls, *, packages: Sequence[str]) -> None:
        """Check that all imports succeed in the specified packages."""
        packages_and_tests = []
        for package in packages:
            if package.startswith("stubs.") or package.startswith("tests."):
                packages_and_tests.append(package)
            else:
                # TODO: Also support tests
                packages_and_tests.extend([package, f"stubs.{package}"])

        # Find import errors in each package
        import_errors = [item for sublist in map(cls._check_package, packages_and_tests) for item in sublist]

        # Report errors
        if import_errors:
            # TODO: Improve formatting of the report
            import_errors_str = "\n".join(import_errors)
            raise RuntimeError(f"Import errors occurred on launch:\n{import_errors_str}\n")

    @classmethod
    def _check_package(cls, package: str) -> list[str]:
        """Check the specified package for import errors."""
        errors: list[str] = []
        try:
            package_import = __import__(package)
        except ImportError as error:
            raise Exception(f"Cannot import module: {error.name}. Check sys.path")

        packages = list(pkgutil.walk_packages(path=package_import.__path__, prefix=package_import.__name__ + "."))
        modules = [x for x in packages if not x.ispkg]
        for m in modules:
            try:
                # Attempt module import
                importlib.import_module(m.name)
            except SyntaxError as error:
                errors.append(
                    f"Cannot import module: {m.name}. Error: {error.msg}. Line: {error.lineno}, {error.offset}"
                )
                continue
            except Exception as error:
                errors.append(f"Cannot import module: {m.name}. Error: {error.args}")

        return errors

    @classmethod
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
                module_name = module_info.name
                # Import the submodule using its full name
                submodule = importlib.import_module(module_name)
                modules.append(submodule)
        return tuple(sorted(modules, key=lambda x: x.__name__))

    @classmethod
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