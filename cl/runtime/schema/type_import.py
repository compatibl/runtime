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
from typing import Callable
from typing import Dict
from typing import Tuple
from cl.runtime.records.protocols import is_data
from cl.runtime.records.protocols import is_enum
from cl.runtime.records.protocols import is_key
from cl.runtime.records.type_util import TypeUtil
from cl.runtime.settings.context_settings import ContextSettings
from cl.runtime.settings.project_settings import ProjectSettings


def is_schema_type(class_: type) -> bool:
    """Return true if the type should be included in schema, includes data classes and enums."""
    return isclass(class_) and (is_data(class_) or is_enum(class_)) and not class_.__name__.endswith("Mixin")


class TypeImport:
    """Helper methods for Record."""

    _type_by_qual_name_dict: Dict[str, type] = {}
    """Dictionary of class types indexed by fully qualified name in module.ClassName format."""

    _type_by_type_name_dict: Dict[str, type] = {}
    """Dictionary of class types indexed by TypeUtil.name(class_)."""

    _module_by_module_name_dict: Dict[str, ModuleType] = {}
    """Dictionary of modules indexed by module name in dot-delimited format."""

    _qual_name_by_type_name_dict: Dict[str, str] | None = None
    """Dictionary of fully qualified names in module.ClassName format indexed by TypeUtil.name(class_)."""

    _cache_filename: str | None = None
    """Filename of the cache file used to store the qual name cache."""

    @classmethod
    def get_qual_name_from_class(cls, class_: type) -> str:
        """Get fully qualified name in module.ClassName format from the class."""
        return f"{class_.__module__}.{class_.__name__}"

    @classmethod
    def get_class_from_qual_name(cls, qual_name: str, *, rebuild_cache: bool = True) -> type:
        """Get class from fully qualified name in module.ClassName format."""

        # Return cached value if found
        if (result := cls._type_by_qual_name_dict.get(qual_name, None)) is not None:
            return result

        # Split fully qualified name into dot-delimited snake_case module and PascalCase class name
        module_name, class_name = qual_name.rsplit(".", 1)

        # Load the module if not already in cache
        if (module := cls._module_by_module_name_dict.get(module_name, None)) is None:
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
                    module = cls._module_by_module_name_dict.setdefault(module_name, import_module(module_name))
                except ModuleNotFoundError:
                    if rebuild_cache:
                        # Rebuild the cache and try again
                        cls.rebuild_cache()
                        return cls.get_class_from_qual_name(qual_name, rebuild_cache=False)
                    else:
                        # Previous attempt to rebuild failed, raise error
                        raise RuntimeError(
                            f"Module not found during type import, run init_import_cache script to rebuild."
                            f"Path to the missing cached module: {module_name}")

        # Get class from module, report error if not found
        try:
            # Get class from module
            result = getattr(module, class_name)
            # Add to the qual_name and type_name dictionaries
            cls._add_class(result)
            return result
        except AttributeError:
            if rebuild_cache:
                # Rebuild the cache and try again
                cls.rebuild_cache()
                return cls.get_class_from_qual_name(qual_name, rebuild_cache=False)
            else:
                # Previous attempt to rebuild failed, raise error
                raise RuntimeError(f"Class not found using qual name: {qual_name}")

    @classmethod
    def get_class_from_type_name(cls, type_name: str, *, rebuild_cache: bool = True) -> type:
        """
        Get class by key generated by TypeUtil.name(class_) method, defaults to
        ClassName except when alias is defined to resolve a name collision.
        """

        # Return cached type if found
        if (result := cls._type_by_type_name_dict.get(type_name, None)) is not None:
            return result

        # Next, try using cached qual name to avoid enumerating classes in all packages
        cls._ensure_cache_loaded()
        if (qual_name := cls._qual_name_by_type_name_dict.get(type_name, None)) is not None:
            return cls.get_class_from_qual_name(qual_name)

        if rebuild_cache:
            # Rebuild the cache and try again
            cls.rebuild_cache()
            return cls.get_class_from_type_name(type_name, rebuild_cache=False)
        else:
            # Previous attempt to rebuild failed, raise error
            raise RuntimeError(f"Class not found using type name: {type_name}")

    @classmethod
    def get_subclasses_of(cls, class_: type, *, predicate: Callable[[type], bool]) -> Tuple[type, ...]:
        """Return a tuple subclasses (inclusive of self) that match the predicate, not cached."""
        # TODO: Add caching, convert to tuple
        # Include self in subclasses
        # Use qual name to exclude duplicates because equality for type is not guaranteed
        result = {TypeImport.get_qual_name_from_class(class_): class_} if predicate(class_) else {}
        for subclass in class_.__subclasses__():
            # Recursively update with non-abstract subclasses
            unfiltered = cls.get_subclasses_of(subclass, predicate=predicate)
            filtered = [x for x in unfiltered if predicate(x)]
            result.update({TypeImport.get_qual_name_from_class(x): x for x in filtered})
        return tuple(result.values())

    @classmethod
    def get_superclasses_of(cls, record_type: type, *, predicate: Callable[[type], bool]) -> Tuple[type, ...]:
        """Return a tuple superclasses (inclusive of self) that match the predicate, not cached."""
        return tuple(x for x in record_type.mro() if predicate(x))

    @classmethod
    def get_records_sharing_key_with(cls, class_: type, *, predicate: Callable[[type], bool]) -> Tuple[type, ...]:
        """Return a tuple of classes sharing key with self (inclusive of self) that match the predicate, not cached."""
        # TODO: Add caching, convert to tuple
        # Find key
        superclasses = cls.get_superclasses_of(class_, predicate=is_key)
        if not superclasses:
            raise RuntimeError(f"Type {TypeUtil.name(class_)} is not derived from a key.")
        elif len(superclasses) != 1:
            keys_str = "\n".join(f"  - {TypeUtil.name(x)}" for x in superclasses)
            raise RuntimeError(f"Type {TypeUtil.name(class_)} has multiple keys among its superclasses:\n{keys_str}\n")
        else:
            # Return subclasses of key type, applying the predicate
            key_type = superclasses[0]
            result = cls.get_subclasses_of(key_type, predicate=predicate)
            return result

    @classmethod
    def get_cached_classes(cls, *, predicate: Callable[[type], bool]) -> Tuple[type, ...]:
        """Return already cached classes that match the predicate (does not rebuild cache)."""
        cls._ensure_cache_loaded()
        # Tuples of (type_name, qual_name) sorted by type name
        sorted_name_pairs = sorted(cls._qual_name_by_type_name_dict.items())
        cached_classes = [cls.get_class_from_qual_name(qual_name) for type_name, qual_name in sorted_name_pairs]
        result = tuple(class_ for class_ in cached_classes if predicate(class_))
        return result

    @classmethod
    def rebuild_cache(cls) -> None:
        """Reload classes from packages and save a new imports.txt file."""

        # Reinitialize the dictionaries
        cls._type_by_qual_name_dict = {}
        cls._type_by_type_name_dict = {}
        cls._module_by_module_name_dict = {}
        cls._qual_name_by_type_name_dict = {}

        # Enumerate modules
        modules = []
        packages = ContextSettings.instance().packages
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

        # Populate the module dictionary
        cls._module_by_module_name_dict = {module.__name__: module for module in modules}

        # Enumerate classes in all modules
        classes = [class_ for module in modules for _, class_ in getmembers(module, is_schema_type)]

        # Add each class after performing checks for duplicates
        tuple(cls._add_class(class_) for class_ in classes)

        # Overwrite the cache file on disk with the new data
        cls._save_cache()

    @classmethod
    def _cached_qual_name_or_none_from_type_name(cls, type_name: str) -> str | None:
        """Attempt to get the qual name from type name, return None if not found."""
        cls._ensure_cache_loaded()
        result = cls._qual_name_by_type_name_dict.get(type_name, None)
        return result

    @classmethod
    def _add_class(cls, class_: type) -> None:
        """Add the specified class to the qual_name and type_name dicts without overwriting the existing values."""
        type_name = TypeUtil.name(class_)
        qual_name = cls.get_qual_name_from_class(class_)
        if (existing_class := cls._type_by_type_name_dict.setdefault(type_name, class_)) == class_:
            # No existing class, add to the dictionaries
            if (existing_class := cls._type_by_qual_name_dict.setdefault(qual_name, class_)) != class_:
                # This should not ordinarily happen, checking for added safety
                raise RuntimeError(
                    f"Two classes share the same fully qualified name:\n"
                    f"  - {cls.get_qual_name_from_class(existing_class)}\n"
                    f"  - {qual_name}\n"
                )
            if (existing_qual_name := cls._qual_name_by_type_name_dict.setdefault(type_name, qual_name)) != qual_name:
                # This should not ordinarily happen, checking for added safety
                raise RuntimeError(
                    f"Two qual names have the same type name, use TypeAlias to resolve the collision: {type_name}\n"
                    f"  - {existing_qual_name}\n"
                    f"  - {qual_name}\n"
                )
        else:
            raise RuntimeError(
                f"Two classes share the same type name, use TypeAlias to resolve the collision: {type_name}\n"
                f"  - {cls.get_qual_name_from_class(existing_class)}\n"
                f"  - {qual_name}\n"
            )

    @classmethod
    def _ensure_cache_loaded(cls) -> None:
        """Load qual name cache from disk if the dict is currently empty."""
        # Do not reload if already loaded
        if cls._qual_name_by_type_name_dict is None:
            cache_filename = cls._get_cache_filename()
            # Do not raise error if the cache file does not exist
            if os.path.exists(cache_filename):
                # Read from the cache file if exists
                with open(cache_filename, "r") as file:
                    rows = file.readlines()
                # Populate the dictionary
                cls._qual_name_by_type_name_dict = {}
                for row in rows:
                    # Remove leading and trailing whitespace from each comma-separated token
                    row_tokens = tuple(x.strip() for x in row.split(","))
                    if len(row_tokens) == 2:
                        # Extract the type name and qual name from the tokens
                        type_name, qual_name = row_tokens
                    else:
                        raise RuntimeError(
                            f"Each row in qual name cache file should contain two comma-separated values.\n"
                            f"Sample row: TypeName,module.ClassName\n"
                            f"Invalid row: {row}\n"
                            f"Qual name cache file: {cache_filename}\n"
                        )
                    if (existing := cls._qual_name_by_type_name_dict.setdefault(type_name, qual_name)) != qual_name:
                        raise RuntimeError(
                            f"Two entries in qualname cache share the same type name: {type_name}\n"
                            f"  - {existing}\n"
                            f"  - {qual_name}\n"
                        )
            else:
                # Cache file does not exist, create an empty dictionary
                cls._qual_name_by_type_name_dict = {}

    @classmethod
    def _save_cache(cls) -> None:
        """Save qual name cache to disk (overwrites the existing file)."""
        # Tuples of (type_name, qual_name) sorted by type name
        sorted_tuples = sorted(cls._qual_name_by_type_name_dict.items())
        cache_filename = cls._get_cache_filename()
        os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
        with open(cache_filename, "w") as file:
            for type_name, qual_name in sorted_tuples:
                file.write(f"{type_name},{qual_name}\n")

    @classmethod
    def _get_cache_filename(cls) -> str:
        """Get the filename for the qual name cache."""
        if cls._cache_filename is None:
            resources_root = ProjectSettings.get_resources_root()
            cls._cache_filename = os.path.join(resources_root, "imports.txt")
        return cls._cache_filename
