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
import os
import sys
from importlib import import_module
from inspect import getmembers
from inspect import isclass
from pkgutil import walk_packages
from types import ModuleType
from typing import Dict
from typing import Sequence
from typing import Tuple
from more_itertools import consume
from cl.runtime.primitive.enum_util import EnumUtil
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_primitive
from cl.runtime.records.protocols import is_record
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.schema.type_kind import TypeKind
from cl.runtime.settings.app_settings import AppSettings
from cl.runtime.settings.project_settings import ProjectSettings


def is_schema_type(class_: type) -> bool:
    """Return true if the type should be included in schema, includes data classes and enums."""
    return isclass(class_) and (is_data(class_) or is_enum(class_)) and not class_.__name__.endswith("Mixin")


_TYPE_INFO_HEADERS = ("TypeName", "TypeKind", "QualName", "ParentNames", "ChildNames")
"""Headers of TypeInfo preload file."""


class TypeCache:
    """Cache of TypeInfo for the specified packages."""

    _type_info_dict: Dict[str, TypeInfo] = {}
    """Dictionary of TypeInfo indexed by type name."""

    _type_by_type_name_dict: Dict[str, type] = {}
    """Dictionary of classes indexed by type name."""

    _type_by_qual_name_dict: Dict[str, type] = {}
    """Dictionary of classes indexed by qual name."""

    _module_dict: Dict[str, ModuleType] = {}
    """Dictionary of modules indexed by module name in dot-delimited format."""

    _packages: Tuple[str, ...] = None
    """List of packages to include in the cache."""

    @classmethod
    def get_qual_name_from_class(cls, class_: type) -> str:
        """Get fully qualified name in module.ClassName format from the class."""
        return f"{class_.__module__}.{class_.__name__}"

    @classmethod
    def get_class_from_qual_name(cls, qual_name: str) -> type:
        """Get class from fully qualified name in module.ClassName format."""

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Return cached value if found
        if (result := cls._type_by_qual_name_dict.get(qual_name, None)) is not None:
            return result

        # Split fully qualified name into dot-delimited snake_case module and PascalCase class name
        module_name, class_name = qual_name.rsplit(".", 1)

        # Load the module if not already in cache
        if (module := cls._module_dict.get(module_name, None)) is None:
            # Check that the module exists and is fully initialized
            module = sys.modules.get(module_name)
            module_spec = getattr(module, "__spec__", None) if module is not None else None
            module_initializing = getattr(module_spec, "_initializing", False) if module_spec is not None else None
            module_imported = module_initializing is False  # To ensure it is not another value evaluating to False

            # Import dynamically if not already imported, report error if not found
            if not module_imported:
                try:
                    # Use setdefault to avoid overwriting the module if
                    # it was added to the cache since the initial check
                    module = cls._module_dict.setdefault(module_name, import_module(module_name))
                except ModuleNotFoundError:
                    raise RuntimeError(
                        f"Module {module_name} is not found in TypeInfo preload, "
                        f"run fix_type_info to regenerate the preload file."
                    )

        # Get class from module, report error if not found
        try:
            # Get class from module
            result = getattr(module, class_name)
            # Add to the qual_name and type_name dictionaries
            cls._add_class(result)
            return result
        except AttributeError:
            raise RuntimeError(
                f"Class {qual_name} is not found in TypeInfo preload,\n"
                f"run fix_type_info to regenerate the preload file."
            )

    @classmethod
    def get_class_from_type_name(cls, type_name: str) -> type:
        """
        Get class by key generated by TypeUtil.name(class_) method, defaults to
        ClassName except when alias is defined to resolve a name collision.
        """

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Return cached type if found
        if (result := cls._type_by_type_name_dict.get(type_name, None)) is not None:
            return result

        # Next, try using cached qual name to avoid enumerating classes in all packages
        if (type_info := cls._type_info_dict.get(type_name, None)) is not None:
            return cls.get_class_from_qual_name(type_info.qual_name)
        else:
            raise cls._type_name_not_found_error(type_name)

    @classmethod
    def get_parent_names(cls, class_: type) -> Tuple[str, ...] | None:
        """Return a tuple of type names for parent classes (inclusive of self) that match the predicate."""

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get from cached TypeInfo
        type_name = TypeUtil.name(class_)
        if (type_info := cls._type_info_dict.get(type_name, None)) is not None:
            return type_info.parent_names
        else:
            raise cls._type_name_not_found_error(type_name)

    @classmethod
    def get_child_names(cls, class_: type) -> Tuple[str, ...] | None:
        """Return a tuple of type names for child classes (inclusive of self) that match the predicate."""

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get from cached TypeInfo
        type_name = TypeUtil.name(class_)
        if (type_info := cls._type_info_dict.get(type_name, None)) is not None:
            return type_info.child_names
        else:
            raise cls._type_name_not_found_error(type_name)

    @classmethod
    def get_classes(cls, *, type_kinds: Sequence[TypeKind]) -> Tuple[type, ...]:
        """Return already cached classes that match the predicate (does not rebuild cache)."""

        # Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded
        cls._ensure_loaded()

        # Get from cached TypeInfo
        qual_names = [x.qual_name for x in cls._type_info_dict.values() if x.type_kind in type_kinds]
        result = tuple(cls.get_class_from_qual_name(qual_name) for qual_name in qual_names)
        return result

    @classmethod
    def rebuild(cls) -> None:
        """Reload classes from packages and save a new TypeInfo.csv file to the bootstrap resources directory."""

        # Clear the existing data
        cls._clear()

        # Add each class after performing checks for duplicates
        consume(cls._add_class(class_) for class_ in cls._get_package_classes())

        # Overwrite the cache file on disk with the new data
        cls._save()

    @classmethod
    def _get_packages(cls) -> Tuple[str, ...]:
        """Get the list of packages specified in settings."""
        if cls._packages is None:
            # Get the list of packages from settings
            cls._packages = tuple(AppSettings.instance().app_packages)
        return cls._packages

    @classmethod
    def _get_package_modules(cls) -> Tuple[ModuleType, ...]:
        """Get the list of modules in the packages specified in settings."""
        modules = []
        packages = cls._get_packages()
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
    def _get_package_classes(cls) -> Tuple[type, ...]:
        """Get the list of classes in the packages specified in settings."""
        # Enumerate classes in all modules that match is_schema_type predicate
        modules = cls._get_package_modules()
        classes = tuple(class_ for module in modules for _, class_ in getmembers(module, is_schema_type))
        return tuple(sorted(classes, key=lambda x: x.__name__))

    @classmethod
    def _get_type_kind(cls, class_: type) -> TypeKind | None:
        """Get type kind of the class, return None if not a framework class."""
        if is_primitive(class_):
            return TypeKind.PRIMITIVE
        elif is_enum(class_):
            return TypeKind.ENUM
        elif is_key(class_):
            return TypeKind.KEY
        elif is_record(class_):
            return TypeKind.RECORD
        elif is_data(class_):
            return TypeKind.DATA
        else:
            # Return None if not a framework class
            return None

    @classmethod
    def _check_class(cls, class_: type) -> None:
        """Check that the class is in the package list."""

        # Error if the class is imported from a module that is not in the package list
        packages = cls._get_packages()
        if not any(class_.__module__.startswith(package) for package in packages):
            packages_str = "\n".join(f"  - {package}" for package in packages)
            raise RuntimeError(
                f"Buildable class {class_.__name__} is declared in module {class_.__module__}\n"
                f"which is not in one of the imported packages. Move the class to an imported package\n"
                f"so it can always be loaded from databases and storage, or exclude it via TypeExclude.csv.\n"
                f"Imported packages:\n{packages_str}"
            )

    @classmethod
    def _build_child_names(cls, class_: type) -> Tuple[str, ...]:
        """Return a tuple subclasses (inclusive of self) that match the predicate, sorted by type name."""
        # This must run after all classes are loaded
        subclasses = [TypeUtil.name(class_)] if is_data(class_) else []  # Include self in subclasses
        for subclass in class_.__subclasses__():
            # Exclude self from subclasses
            if subclass is not class_:
                # Check that the subclass is in the package list
                cls._check_class(subclass)
                # Recurse into the subclass hierarchy, avoid adding duplicates
                subclasses.extend(x for x in cls._build_child_names(subclass) if x not in subclasses)
        # Eliminate duplicates (they should not be present but just to be sure) and sort the names
        return tuple(sorted(set(subclasses)))

    @classmethod
    def _build_parent_names(cls, class_: type) -> Tuple[str, ...]:
        """Return a tuple superclasses (inclusive of self) that match the predicate, not cached."""
        # Eliminate duplicates (they should not be present but just to be sure) and sort the names in MRO list
        return tuple(sorted(set(TypeUtil.name(x) for x in class_.mro() if is_data(x))))

    @classmethod
    def _add_class(cls, class_: type, *, subtype: str | None = None) -> None:
        """Add the specified class to the qual_name and type_name dicts without overwriting the existing values."""

        # TODO: Exclude classes in TypeExclude.csv

        # Error if the class is imported from a module that is not in the package list
        cls._check_class(class_)

        type_kind = cls._get_type_kind(class_)
        if type_kind is None:
            # Skip if not a framework class
            return

        if type_kind == TypeKind.PRIMITIVE:
            # Apply subtype if specified for a primitive type
            type_name = subtype if subtype else class_.__name__
        else:
            # Get type name with aliases applied
            type_name = TypeUtil.name(class_)
            # Ensure subtype is not specified for non-primitive types
            if subtype:
                raise RuntimeError(
                    f"Subtype {subtype} is specified for non-primitive class {class_.__name__}.\n"
                    f"Only primitive types can have subtypes."
                )

        # Get fully qualified name
        qual_name = cls.get_qual_name_from_class(class_)

        # Get parent and child class names for data, keys or records
        if is_data(class_):
            # Build parent and child name lists
            parent_names = cls._build_parent_names(class_)
            child_names = cls._build_child_names(class_)

            # Use None if empty
            parent_names = parent_names if parent_names else None
            child_names = child_names if child_names else None
        else:
            # Do not generate if not data
            parent_names = None
            child_names = None

        # Get type info without subclass names (which will be done on second pass after all classes are loaded)
        type_info = TypeInfo(
            type_name=type_name,
            type_kind=type_kind,
            qual_name=qual_name,
            parent_names=parent_names,
            child_names=child_names,
        )

        # Populate the dictionary
        existing_info = cls._type_info_dict.setdefault(type_info.type_name, type_info)

        # Check for duplicate type names
        if existing_info.qual_name != type_info.qual_name:
            packages_str = ", ".join(cls._get_packages())
            raise RuntimeError(
                f"Two classes in the package list share the same type name: {type_info.type_name}\n"
                f"  - {existing_info.qual_name}\n"
                f"  - {type_info.qual_name}\n"
                f"Package list: {packages_str}\n"
                f"Use TypeAlias to resolve the name collision.\n"
            )

    @classmethod
    def _ensure_loaded(cls):
        """Ensure the type cache is loaded from TypeInfo.csv, will not reload if already loaded."""
        if not cls._type_info_dict:
            # Load the type cache from TypeInfo.csv
            cls._load()

    @classmethod
    def _load(cls) -> None:
        """Load type cache from TypeInfo.csv."""

        # Clear cache before loading
        cls._clear()

        # Read from the cache file
        cache_filename = cls._get_preload_filename()
        if os.path.exists(cache_filename):
            with open(cache_filename, "r") as file:
                rows = file.readlines()
        else:
            # Cache file does not exist, error message
            raise RuntimeError(f"Cache file is not found at {cache_filename}\n, run fix_type_info to regenerate.")

        # Iterate over the rows of TypeInfo preload
        for row_index, row in enumerate(rows):

            # Remove leading and trailing whitespace from each comma-separated token
            row_tokens = tuple(x.strip() for x in row.split(","))

            if row_index == 0:
                # Check that the header row has expected values
                if row_tokens != _TYPE_INFO_HEADERS:
                    actual_headers_str = ", ".join(row_tokens)
                    expected_headers_str = ", ".join(_TYPE_INFO_HEADERS)
                    raise RuntimeError(
                        f"TypeInfo preload file has invalid headers.\n"
                        f"Preload file: {cache_filename}\n"
                        f"Actual headers: {actual_headers_str}\n"
                        f"Expected headers: {expected_headers_str}\n"
                    )
            else:
                # Parse a type info row
                if len(row_tokens) == len(_TYPE_INFO_HEADERS):
                    # Extract the type name and qual name from the tokens
                    type_name, type_kind, qual_name, parent_names, child_names = row_tokens
                else:
                    expected_num_tokens = len(_TYPE_INFO_HEADERS)
                    actual_num_tokens = len(row_tokens)
                    raise RuntimeError(
                        f"Invalid number of comma-delimited tokens {actual_num_tokens} in TypeInfo preload, "
                        f"should be {expected_num_tokens}.\n"
                        f"Sample row: TypeName,TypeKind,module.ClassName,Superclass1;Superclass2,Subclass1;Subclass2,\n"
                        f"Invalid row: {row.strip()}\n"
                    )

                # Create type info object without child class names
                type_info = TypeInfo(
                    type_name=type_name,
                    type_kind=EnumUtil.from_str(TypeKind, type_kind),
                    qual_name=qual_name,
                    parent_names=tuple(parent_names.split(";")) if parent_names else None,
                    child_names=tuple(child_names.split(";")) if child_names else None,
                )

                # Add to the type info dictionary
                existing = cls._type_info_dict.setdefault(type_info.type_name, type_info)

                # Check for duplicates
                if existing.qual_name != type_info.qual_name:
                    raise RuntimeError(
                        f"Two entries in TypeInfo preload share the same type name: {type_name}\n"
                        f"  - {existing.qual_name}\n"
                        f"  - {type_info.qual_name}\n"
                        f"Use TypeAlias to resolve the name collision.\n"
                    )

    @classmethod
    def _save(cls) -> None:
        """Save qual name cache to disk (overwrites the existing file)."""
        # Tuples of (type_name, qual_name) sorted by type name
        cache_filename = cls._get_preload_filename()
        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w") as file:
            # Write header row
            file.write(",".join(_TYPE_INFO_HEADERS) + "\n")

            # Sort the TypeInfo dictionary by type name and iterate
            sorted_type_info_list = sorted(cls._type_info_dict.values(), key=lambda x: x.type_name)
            for type_info in sorted_type_info_list:

                # Format fields for writing
                type_name = type_info.type_name
                type_kind_str = EnumUtil.to_str(type_info.type_kind)
                qual_name = type_info.qual_name

                # Sort parent and child names (they should already be sorted, just to be sure)
                parent_names_str = ";".join(sorted(type_info.parent_names)) if type_info.parent_names else ""
                child_names_str = ";".join(sorted(type_info.child_names)) if type_info.child_names else ""

                # Write comma-separated values for each token, with semicolons-separated lists
                file.write(f"{type_name},{type_kind_str},{qual_name},{parent_names_str},{child_names_str}\n")

    @classmethod
    def _clear(cls) -> None:
        """Clear cache before loading or rebuilding."""
        cls._type_info_dict = {}
        cls._type_by_type_name_dict = {}
        cls._type_by_qual_name_dict = {}
        cls._module_dict = {}
        cls._cache_filename = None

    @classmethod
    def _get_preload_filename(cls) -> str:
        """Get the filename for the qual name cache."""
        resources_root = ProjectSettings.get_resources_root()
        result = os.path.join(resources_root, "bootstrap/TypeInfo.csv")
        return result

    @classmethod
    def _type_name_not_found_error(cls, type_name: str) -> RuntimeError:
        """Return error message for type name not found."""
        return RuntimeError(
            f"Type {type_name} is not found in TypeInfo preload,\n" f"run fix_type_info to regenerate the preload file."
        )
