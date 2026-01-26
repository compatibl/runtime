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

import pytest
import os
from cl.runtime.project.project_layout import ProjectLayout
from cl.runtime.qa.regression_guard import RegressionGuard
from cl.runtime.storage.local_storage import LocalStorage
from cl.runtime.storage.storage_mode import StorageMode

_SAMPLE_REL_PATHS = (
    "sample_file",
    "sample_dir/sample_file",
)

_EXCEPTION_REL_PATHS = (
    "/sample_file",  # Absolute path
    "/sample_dir/sample_file",  # Absolute path
)


def test_local_storage():
    """Test LocalTextFile class."""

    guard = RegressionGuard().build()
    abs_dir = guard.get_output_dir()
    rel_dir = os.path.relpath(abs_dir, start=ProjectLayout.get_project_root())
    extensions = ("txt", "bin")
    with LocalStorage(rel_dir=rel_dir).build() as storage:
        for extension in extensions:
            for index, rel_path in enumerate(_SAMPLE_REL_PATHS):
                rel_path = f"{rel_path}.{extension}"

                # Delete the exiting file
                abs_path = os.path.join(abs_dir, rel_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)

                if extension == "txt":
                    open_callable = storage.open_text_file
                    mode_suffix = ""
                elif extension == "bin":
                    open_callable = storage.open_binary_file
                    mode_suffix = "b"
                else:
                    raise ValueError(f"Unsupported file extension in a text: {extension}")

                # Test write and append operations
                with open_callable(rel_path, "w" + mode_suffix) as f:
                    data = "Hello, world!"
                    if extension == "bin":
                        data = data.encode()
                    f.write(data)
                with open_callable(rel_path, "a" + mode_suffix) as f:
                    data = "Hello again, world!"
                    if extension == "bin":
                        data = data.encode()
                    f.write(data)
                with open_callable(rel_path, "r" + mode_suffix) as f:
                    read_result = f.read()
                    if index == 0:
                        if extension == "bin":
                            read_result = read_result.decode()
                        guard.write(read_result)
                with open_callable(rel_path, "w" + mode_suffix) as f:
                    data = "Overwriting the file"
                    if extension == "bin":
                        data = data.encode()
                    f.write(data)
                with open_callable(rel_path, "r" + mode_suffix) as f:
                    read_result = f.read()
                    if index == 0:
                        if extension == "bin":
                            read_result = read_result.decode()
                        guard.write(read_result)
    RegressionGuard.verify_all()


def test_local_storage_exceptions():

    # Test invalid storage modes
    guard = RegressionGuard().build()
    abs_dir = guard.get_output_dir()
    rel_dir = os.path.relpath(abs_dir, start=ProjectLayout.get_project_root())
    extensions = ("txt", "bin")
    with LocalStorage(rel_dir=rel_dir, storage_mode=StorageMode.READ_ONLY).build() as storage:
        with pytest.raises(Exception):
            storage.open_text_file(_SAMPLE_REL_PATHS[0], "w")
        with pytest.raises(Exception):
            storage.open_text_file(_SAMPLE_REL_PATHS[0], "a")
        with pytest.raises(Exception):
            storage.open_binary_file(_SAMPLE_REL_PATHS[0], "wb")
        with pytest.raises(Exception):
            storage.open_binary_file(_SAMPLE_REL_PATHS[0], "ab")

    # Test invalid file modes
    with LocalStorage(rel_dir=rel_dir).build() as storage:
        with pytest.raises(Exception):
            storage.open_binary_file(_SAMPLE_REL_PATHS[0], "r")
        with pytest.raises(Exception):
            storage.open_binary_file(_SAMPLE_REL_PATHS[0], "w")
        with pytest.raises(Exception):
            storage.open_binary_file(_SAMPLE_REL_PATHS[0], "a")
        with pytest.raises(Exception):
            storage.open_text_file(_SAMPLE_REL_PATHS[0], "rb")
        with pytest.raises(Exception):
            storage.open_text_file(_SAMPLE_REL_PATHS[0], "wb")
        with pytest.raises(Exception):
            storage.open_text_file(_SAMPLE_REL_PATHS[0], "ab")

    # Test invalid paths
    with LocalStorage(rel_dir=rel_dir).build() as storage:
        with pytest.raises(Exception):
            # Absolute paths are not allowed
            storage.open_text_file("/sample.txt", "r")
        with pytest.raises(Exception):
            # Absolute paths are not allowed
            storage.open_text_file("/sample_dir/sample.txt", "r")


if __name__ == "__main__":
    pytest.main([__file__])
