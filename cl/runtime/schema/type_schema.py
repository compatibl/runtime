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

import dataclasses
import datetime as dt
import importlib
import inspect
from collections import Counter
from dataclasses import is_dataclass
from enum import Enum
from pkgutil import walk_packages
from types import ModuleType
from typing import Type, List, Dict, Iterable, Tuple, Mapping
from uuid import UUID

from frozendict import frozendict

from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.dataclass_spec import DataclassSpec
from cl.runtime.schema.enum_spec import EnumSpec
from cl.runtime.schema.primitive_spec import PrimitiveSpec
from cl.runtime.schema.type_spec import TypeSpec
from cl.runtime.settings.context_settings import ContextSettings

def is_schema_type(data_type) -> bool:
    """Return true if the type should be included in schema, includes classes with build method and enums."""
    return inspect.isclass(data_type) and (hasattr(data_type, "build") or issubclass(data_type, Enum))

class TypeSchema:
    """
    Provides information about a type included in schema and its dependencies including data types,
    enums and primitive types.
    """

    _spec_dict: Dict[str, TypeSpec] = {
        "str": PrimitiveSpec.from_class(str),
        "float": PrimitiveSpec.from_class(float),
        "bool": PrimitiveSpec.from_class(bool),
        "int": PrimitiveSpec.from_class(int),
        "long": PrimitiveSpec.from_class(int, subtype="long"),
        "date": PrimitiveSpec.from_class(dt.date),
        "time": PrimitiveSpec.from_class(dt.time),
        "datetime": PrimitiveSpec.from_class(dt.datetime),
        "UUID": PrimitiveSpec.from_class(UUID),
        "timestamp": PrimitiveSpec.from_class(UUID, subtype="timestamp"),
        "bytes": PrimitiveSpec.from_class(float),
    }
    """Dictionary of type specs indexed by type name and initialized with primitive types."""

    _class_dict: Mapping[str, Type] | None = None
    """Dictionary of types indexed by class name."""
    
    _modules: Tuple[ModuleType, ...] | None = None
    """Modules from the packages specified in the settings."""
    
    _packages: Tuple[str, ...] | None = None
    """Packages specified in the settings."""

    @classmethod
    def get_type_spec(cls, type_name: str) -> TypeSpec:
        """Get or create type spec for the specified type name."""

        if (result := cls._spec_dict.get(type_name, None)) is not None:

            # Already created, return from spec dictionary
            return result
        else:

            # Get class for the specified type name
            class_ = cls.get_class(type_name)

            # Get class for the type spec
            if issubclass(class_, Enum):
                spec_class = EnumSpec
            elif dataclasses.is_dataclass(class_):
                spec_class = DataclassSpec
            else:
                raise RuntimeError(f"Class {class_.__name__} implements build method but does not\n"
                                   f"use one of the supported dataclass frameworks and does not\n"
                                   f"have a method to generate type spec.")

            # Create from class, add to spec dictionary and return
            result = spec_class.from_class(class_)
            cls._spec_dict[type_name] = result
            return result

    @classmethod
    def get_class(cls, type_name) -> Type:
        """Get class for the specified type name, excludes primitive types."""

        # Get or create type dictionary
        type_dict = cls.get_class_dict()

        if (result := type_dict.get(type_name, None)) is not None:
            return result
        else:
            packages_str = "\n".join(cls._get_packages())
            raise RuntimeError(f"Type {type_name} is not found in the packages specified in settings:\n{packages_str}")

    @classmethod
    def _get_packages(cls) -> Iterable[str]:
        """Get the list of packages specified in the settings."""
        if (result := cls._packages) is None:
            context_settings = ContextSettings.instance()
            result = context_settings.packages
            cls._packages = result
        return result

    @classmethod
    def _get_modules(cls) -> Iterable[ModuleType]:
        """
        Get a list of ModuleType objects for submodules at all levels of the specified packages or root modules
        in the alphabetical order of dot-delimited module name.
        """

        if (result := cls._modules) is None:
            
            result = []
            packages = cls._get_packages()
            for package in packages:
                # Import root module of the package
                root_module = importlib.import_module(package)
                # Add the root module itself
                result.append(root_module)  
                # Get module info for all submodules, note the trailing period added per walk_packages documentation
                for module_info in walk_packages(root_module.__path__, root_module.__name__ + "."):
                    module_name = module_info.name
                    # Import the submodule using its full name
                    submodule = importlib.import_module(module_name)
                    result.append(submodule)
    
            # Sort the result by module path
            result = tuple(sorted(result, key=lambda module: module.__name__))
            cls._modules = result
        return result

    @classmethod
    def get_class_dict(cls) -> Dict[str, Type]:
        """Get or create a dictionary of types indexed by their name, excludes primitive types."""

        if (result := cls._class_dict) is None:

            # Get modules for the packages specified in the settings
            modules = TypeSchema._get_modules()

            # Get classes by iterating over modules
            classes = set(
                class_
                for module in modules
                for name, class_ in inspect.getmembers(module, is_schema_type)
            )

            # Use namespace alias to resolve conflicts
            class_names = [TypeUtil.name(record_type) for record_type in classes]

            # Check that there are no repeated names, report errors if there are
            if len(set(class_names)) != len(class_names):

                # Count the occurrences of each name in the list
                class_name_counts = Counter(class_names)

                # Find names and their types that are repeated more than once
                repeated_names = [class_name for class_name, count in class_name_counts.items() if count > 1]

                # Report repeated names
                repeated_type_reports = "\n".join(
                    repeated_name
                    + ": "
                    + ", ".join(
                        f"{x.__module__}.{x.__name__}" for x in classes if TypeUtil.name(x) == repeated_name
                    )
                    for repeated_name in repeated_names
                )
                raise RuntimeError(f"The following class names are not unique:\n{repeated_type_reports}\n")

            # Create and cache the result
            result = frozendict(zip(class_names, classes))
            cls._class_dict = result

        return result
