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

import difflib
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import ClassVar
from typing import Dict
from typing import Literal
import yaml
from typing_extensions import Self
from cl.runtime.context.env_util import EnvUtil
from cl.runtime.records.protocols import is_key
from cl.runtime.records.protocols import is_record
from cl.runtime.schema.field_decl import primitive_types
from cl.runtime.serialization.dict_serializer import DictSerializer
from cl.runtime.serialization.string_serializer import StringSerializer

_supported_extensions = ["txt", "yaml"]
"""The list of supported output file extensions (formats)."""

key_serializer = StringSerializer()
"""Serializer for keys."""

data_serializer = DictSerializer()
"""Serializer for records."""


# Custom Dumper to ensure proper block style for multi-line strings
class NoExtraLineBreakDumper(yaml.Dumper):
    def represent_scalar(self, tag, value, style=None):
        """Use block style (|) for multiline strings."""
        if '\n' in value:
            style = '|'
        return super().represent_scalar(tag, value, style)


def _error_extension_not_supported(ext: str) -> Any:
    raise RuntimeError(
        f"Extension {ext} is not supported by RegressionGuard. "
        f"Supported extensions: {', '.join(_supported_extensions)}"
    )


@dataclass(slots=True, init=False)
class RegressionGuard:
    """
    Detects changes (regression) of output across multiple channels during unit testing.

    Notes:
        - Channel name is module.test_function or module.test_class.test_method
        - The output is recorded in 'channel.received.ext' located next to the unit test
        - If 'channel.expected.ext' does not exist, it is created with the same data as 'channel.received.ext'
        - Otherwise, the test fails if 'channel.expected.ext' and 'channel.received.ext' differ
        - To record a new 'channel.expected.ext' file, delete the existing one
        - File extension 'ext' is determined based on the verify method(s) called
    """

    base_path: str
    """Base path for the text excluding the channel, 'verify_all' method applies to all subdirs or this dir."""

    output_path: str
    """Output path for the test and channel, 'verify' method applies to this dir only."""

    ext: str
    """Output file extension (format), defaults to '.txt'"""

    __verified: bool
    """Verify method sets this flag to true, after which further writes raise an error."""

    __exception_text: str | None
    """Exception text from an earlier verification is reused instead of comparing the files again."""

    __delegate_to: Self | None
    """Delegate all function calls to this regression guard if set (instance vars are not initialized in this case)."""

    __guard_dict: ClassVar[Dict[str, Dict[str, Self]]] = {}  # TODO: Set using ContextVars
    """Dictionary of existing guards indexed by base_path (outer dict) and channel/ext (inner dict)."""

    def __init__(
        self,
        *,
        ext: str = None,
        channel: str | None = None,
        test_function_pattern: str | None = None,
    ):
        """
        Initialize the regression guard, optionally specifying channel.

        Args:
            ext: File extension (format) without the dot prefix, defaults to 'txt'
            channel: Dot-delimited string for the channel or None for no channel
            test_function_pattern: Glob pattern for function or method in stack frame, defaults to 'test_*'
        """

        # Find base path by examining call stack
        base_path = EnvUtil.get_env_dir(test_function_pattern=test_function_pattern)

        # Make channel the filename prefix with dot delimiter if specified
        if channel is not None and channel != "":
            output_path = os.path.join(base_path, f"{channel}.")
        else:
            output_path = os.path.join(base_path, "")

        if ext is not None:
            # Remove dot prefix if specified
            ext = ext.removeprefix(".")
            if ext not in _supported_extensions:
                _error_extension_not_supported(ext)
        else:
            # Use txt if not specified
            ext = "txt"

        # Get inner dictionary using base path
        inner_dict = self.__guard_dict.setdefault(base_path, dict())

        # Check if regression guard already exists in inner dictionary for the same combination of channel and ext
        inner_key = f"{channel}::{ext}"
        if (existing_dict := inner_dict.get(inner_key, None)) is not None:
            # Delegate to the existing guard if found, do not initialize other fields
            self.__delegate_to = existing_dict
        else:
            # Otherwise add self to dictionary
            inner_dict[inner_key] = self

            # Initialize fields
            self.__delegate_to = None
            self.__verified = False
            self.__exception_text = None
            self.base_path = base_path
            self.output_path = output_path
            self.ext = ext

            # Delete the existing received file if exists
            if os.path.exists(received_path := self._get_file_path("received")):
                os.remove(received_path)

    def write(self, value: Any) -> None:
        """
        Record the argument for regression testing purposes.

        Args:
            value: Data to be recorded, accepted data types depend on the specified file extension
        """

        # Perform type conversion
        if isinstance(value, Exception):
            value = f"Raises {type(value).__name__} with the message:\n{str(value)}"

        # Delegate to a previously created guard with the same combination of output_path and ext if exists
        if self.__delegate_to is not None:
            self.__delegate_to.write(value)
            return

        if self.__verified:
            raise RuntimeError(
                f"Regression output file {self._get_file_path('received')} is already verified "
                f"and can no longer be written to."
            )

        received_path = self._get_file_path("received")
        received_dir = os.path.dirname(received_path)
        if not os.path.exists(received_dir):
            # Create the directory if does not exist
            os.makedirs(received_dir)

        if self.ext == "txt" or self.ext == "yaml":
            with open(received_path, "a") as file:
                file.write(self._format_txt(value))
                # Flush immediately to ensure all of the output is on disk in the event of test exception
                file.flush()
        else:
            # Should not be reached here because of a previous check in __init__
            _error_extension_not_supported(self.ext)

    def verify_all(self, *, silent: bool = False) -> bool:
        """
        Verify for all guards in this test that 'channel.received.ext' is the same as 'channel.expected.ext'.
        Defaults to silent=True (no exception) to permit other tests to proceed.

        Notes:
            - If 'channel.expected.ext' does not exist, create from 'channel.received.ext'
            - If files are the same, delete 'channel.received.ext' and 'channel.diff.ext'
            - If files differ, write 'channel.diff.ext' and raise exception unless silent=True

        Returns:
            bool: True if verification succeeds and false otherwise

        Args:
            silent: If true, do not raise exception and only write the 'channel.diff.ext' file
        """

        # Delegate to a previously created guard with the same combination of output_path and ext if exists
        if self.__delegate_to is not None:
            return self.__delegate_to.verify_all(silent=silent)

        # Get inner dictionary using base path
        inner_dict = self.__guard_dict[self.base_path]

        # Skip the delegated guards
        inner_dict = {k: v for k, v in inner_dict.items() if v.__delegate_to is None}

        # Call verify for all guards silently and check if all are true
        # Because 'all' is used, the comparison will not stop early
        errors_found = not all(guard.verify(silent=True) for guard in inner_dict.values())

        if errors_found and not silent:
            # Collect exception text from guards where it is present
            exc_text_blocks = [
                exception_text
                for guard in inner_dict.values()
                if (exception_text := guard._get_exception_text()) is not None
            ]

            # Merge the collected exception text blocks and raise an error
            exc_text_merged = "\n".join(exc_text_blocks)
            raise RuntimeError(exc_text_merged)

        return not errors_found

    def verify(self, *, silent: bool = False) -> bool:
        """
        Verify for this regression guard that 'channel.received.ext' is the same as 'channel.expected.ext'.
        Defaults to silent=True (no exception) to permit other tests to proceed.

        Notes:
            - If 'channel.expected.ext' does not exist, create from 'channel.received.ext'
            - If files are the same, delete 'channel.received.ext' and 'channel.diff.ext'
            - If files differ, write 'channel.diff.ext' and raise exception unless silent=True

        Returns:
            bool: True if verification succeeds and false otherwise

        Args:
            silent: If true, do not raise exception and only write the 'channel.diff.ext' file
        """

        # Delegate to a previously created guard with the same combination of output_path and ext if exists
        if self.__delegate_to is not None:
            return self.__delegate_to.verify(silent=silent)

        if self.__verified:
            # Already verified
            if not silent:
                # Use the existing exception text to raise if silent=False
                raise RuntimeError(self.__exception_text)
            else:
                # Otherwise return True if exception text is None (it is set on verification failure)
                return self.__exception_text is None

        received_path = self._get_file_path("received")
        expected_path = self._get_file_path("expected")
        diff_path = self._get_file_path("diff")

        # If received file does not yet exist, return True
        if not os.path.exists(received_path):
            # Do not set the __verified flag so that verification can be performed again at a later time
            return True

        if os.path.exists(expected_path):

            # Read both files
            with open(received_path, "r") as received_file:
                received_lines = list(received_file.readlines())
            with open(expected_path, "r") as expected_file:
                expected_lines = list(expected_file.readlines())

            # Expected file exists, ensure all lines match
            if all(x == y for x, y in zip(received_lines, expected_lines)):
                # All received and expected lines match, delete the received file and diff file
                os.remove(received_path)
                if os.path.exists(diff_path):
                    os.remove(diff_path)

                # Return True to indicate verification has been successful
                return True
            else:
                # Some of the lines do not match, generate unified diff
                # TODO: Handle diff for binary output
                # Convert to list first because the returned object is a generator but
                # we will need to iterate over the lines more than once
                diff = list(
                    difflib.unified_diff(
                        expected_lines, received_lines, fromfile=expected_path, tofile=received_path, n=0
                    )
                )

                # Write the complete unified diff into to the diff file
                with open(diff_path, "w") as diff_file:
                    diff_file.write("".join(diff))

                # Truncate to max_lines and surround by begin/end lines for generate exception text
                line_len = 120
                max_lines = 5
                begin_str = "BEGIN REGRESSION TEST UNIFIED DIFF "
                end_str = "END REGRESSION TEST UNIFIED DIFF "
                begin_sep = "-" * (line_len - len(begin_str))
                end_sep = "-" * (line_len - len(end_str))
                orig_lines = len(diff)
                if orig_lines > max_lines:
                    diff = diff[:max_lines]
                    truncate_str = f"(TRUNCATED {orig_lines-max_lines} ADDITIONAL LINES) "
                    end_sep = end_sep[: -len(truncate_str)]
                else:
                    truncate_str = ""
                diff_str = "".join(diff)
                exception_text = f"\n{begin_str}{begin_sep}\n" + diff_str
                extra_eol = "" if exception_text.endswith("\n") else "\n"
                exception_text = exception_text + f"{extra_eol}{end_str}{truncate_str}{end_sep}"

                # Record into the object even if silent
                self.__exception_text = exception_text

                # Set the __verified flag so that verification returns the same result if attempted again
                # This will prevent further writes to this channel and extension
                self.__verified = True

                if not silent:
                    # Raise exception only when not silent
                    raise RuntimeError(exception_text)
                else:
                    return False
        else:
            # Expected file does not exist, copy the data from received to expected
            with open(received_path, "rb") as received_file, open(expected_path, "wb") as expected_file:
                expected_file.write(received_file.read())

            # Delete the received file and diff file
            os.remove(received_path)
            if os.path.exists(diff_path):
                os.remove(diff_path)

            # Set the __verified flag so that verification returns the same result if attempted again
            # This will prevent further writes to this channel and extension
            self.__verified = True

            # Verification is considered successful if expected file has been created
            self.__verified = True
            return True

    def _format_txt(self, value: Any) -> str:
        """Format text for regression testing."""

        # Convert to one of the supported output types
        if is_record(value):
            value = data_serializer.serialize_data(value)
        elif is_key(value):
            value = key_serializer.serialize_key(value)

        value_type = type(value)
        if value_type in primitive_types:
            # TODO: Use specialized conversion for primitive types
            return str(value) + "\n"
        elif value_type == dict:
            return yaml.dump(
                value,
                Dumper=NoExtraLineBreakDumper,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,  # Ensure Unicode characters are displayed as is
                width=float("inf"),  # Prevent line wrapping
            ) + "\n"
        elif issubclass(value_type, Enum):
            return str(value)
        elif hasattr(value_type, "__iter__"):
            return "\n".join(map(self._format_txt, value)) + "\n"
        else:
            raise RuntimeError(
                f"Argument type {value_type} is not accepted for file extension '{self.ext}'. "
                f"Valid arguments are primitive types, dict, or their iterable."
            )

    def _get_exception_text(self) -> str | None:
        """Get exception text from this guard or the guard it delegates to."""
        if self.__delegate_to is not None:
            # Get from the guard this guard delegates to
            return self.__delegate_to._get_exception_text()
        else:
            # Get from this guard
            return self.__exception_text

    def _get_file_path(self, file_type: Literal["received", "expected", "diff"]) -> str:
        """The diff between received and expected is written to 'channel.diff.ext' located next to the unit test."""
        result = f"{self.output_path}{file_type}.{self.ext}"
        return result
