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
import hashlib
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import ClassVar
from typing import Self
from cl.runtime.qa.qa_util import QaUtil
from cl.runtime.qa.png_util import PngUtil
from cl.runtime.records.bootstrap_mixin import BootstrapMixin
from cl.runtime.records.protocols import MAPPING_TYPES
from cl.runtime.records.protocols import SEQUENCE_TYPES
from cl.runtime.records.protocols import is_key_type
from cl.runtime.records.protocols import is_record_type
from cl.runtime.records.typename import typename
from cl.runtime.schema.field_decl import primitive_types
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers

_supported_extensions = ["txt", "yaml", "html", "png"]
"""The list of supported output file extensions (formats)."""

_KEY_SERIALIZER = KeySerializers.DELIMITED
"""Serializer for keys."""

_YAML_SERIALIZER = BootstrapSerializers.YAML
"""Serializer for classes and containers."""


@dataclass(slots=True, kw_only=True)
class RegressionGuard(BootstrapMixin):
    """
    Detects changes (regression) of multiple output files per unit test.

    Notes:
        - If param use_hash=True, output has extension ".sha256" but received file has original ext in case of diff
        - Output files are '{prefix}.expected.ext' and '{prefix}.received.ext', or 'expected.ext' and 'received.ext'
          if prefix is None
        - If '{prefix}.expected.ext' does not exist, it is created with the same data as '{prefix}.received.ext'
        - Otherwise, the test fails if '{prefix}.expected.ext' and '{prefix}.received.ext' differ
        - To record a new '{prefix}.expected.ext' file, delete the existing one
    """

    prefix: str | None = None
    """Regression file prefix, use when a single test produces more than one regression file."""

    ext: str = "txt"
    """Output file extension without the leading dot, defaults to 'txt'."""

    use_hash: bool | None = None
    """If True, verify using SHA256 hash comparison instead of full file comparison (defaults to None)."""

    _output_dir: str | None = None
    """Absolute path to the test output directory, 'verify_all' method applies everything in this directory."""

    _output_dir_and_prefix: str | None = None
    """Combines _output_dir and prefix, 'verify' method applies to file with this prefix only."""

    _verified: bool | None = None
    """Verify method sets this flag to true, after which further writes raise an error."""

    _exception_text: str | None = None
    """Exception text from an earlier verification is reused instead of comparing the files again."""

    _delegate_to: Self | None = None
    """Delegate all function calls to this regression guard if set (instance vars are not initialized in this case)."""

    _guard_dict: ClassVar[dict[str, dict[str | None, Self]]] = {}  # TODO: Define using ContextVars for multithreading
    """Dictionary of existing guards indexed by output_dir (outer dict) and prefix (inner dict)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        # Find base path by examining call stack
        self._output_dir = QaUtil.get_test_dir_from_call_stack()

        # Use filename prefix with dot delimiter if specified
        if self.prefix is not None and self.prefix != "":
            self._output_dir_and_prefix = os.path.join(self._output_dir, f"{self.prefix}.")
        else:
            self._output_dir_and_prefix = os.path.join(self._output_dir, "")

        if self.ext is not None:
            # Remove dot prefix if specified
            self.ext = self.ext.removeprefix(".")
            if self.ext not in _supported_extensions:
                self._error_extension_not_supported(self.ext)
        else:
            raise RuntimeError("Param 'ext' is not specified in RegressionGuard.")

        # Get inner dictionary using _output_dir
        inner_dict = self._guard_dict.setdefault(self._output_dir, dict())

        # Check if regression guard already exists in inner dictionary for the same combination of prefix, ext, use_hash
        if (existing_guard := inner_dict.get(self.prefix, None)) is not None:
            # Delegate to the existing guard if found
            self._delegate_to = existing_guard
            if self.ext != existing_guard.ext:
                raise RuntimeError(
                    f"Two RegressionGuard instances for the same output directory and prefix\n"
                    f"have different file extensions.\nOutput directory: {self._output_dir}\nPrefix: {self.prefix}\n"
                    f"Extensions: {self.ext}, {existing_guard.ext}\n"
                )
            if self.use_hash != existing_guard.use_hash:
                raise RuntimeError(
                    f"Two RegressionGuard instances for the same output directory and prefix\n"
                    f"have different values of use_hash.\nOutput directory: {self._output_dir}\nPrefix: {self.prefix}\n"
                )
        else:
            # Otherwise add self to dictionary of guards for this output dir
            inner_dict[self.prefix] = self

            # Delete the existing received file if exists
            if os.path.exists(received_path := self._get_file_path("received")):
                os.remove(received_path)

    def get_output_dir(self) -> str:
        """Return absolute output directory path."""
        self.check_frozen()
        return self._output_dir

    def write(self, value: Any) -> Self:
        """
        Record the argument for regression testing purposes.

        Args:
            value: Data to be recorded, accepted data types depend on the specified file extension

        Returns:
            Self for method call chaining, will return delegated to guard in case of delegation
        """
        self.check_frozen()

        # Perform type conversion
        if isinstance(value, Exception):
            value = f"Raises {typename(type(value))} with the message:\n{str(value)}"

        # Delegate to a previously created guard with the same output_path if it exists
        if self._delegate_to is not None:
            # Invoke write on the delegated to guard and return that guard
            return self._delegate_to.write(value)

        received_path = self._get_file_path("received")
        if self._verified:  # TODO: Improve logic to avoid rerunning in this case
            raise RuntimeError(
                f"Cannot write to a received file for RegressionGuard because a difference between\n"
                f"received and expected file occurred during a previous test for the same file,\n"
                f"or the expected file was not found. Rerun the test if this occurred during\n"
                f"the creation of the expected file.\n"
                f"File path: {received_path}"
            )

        received_dir = os.path.dirname(received_path)
        if not os.path.exists(received_dir):
            # Create the directory if does not exist
            os.makedirs(received_dir)

        if self.ext == "txt" or self.ext == "yaml":
            with open(received_path, "a", encoding="utf-8") as file:
                file.write(self._format_txt(value))
                # Flush immediately to ensure all of the output is on disk in the event of test exception
                file.flush()
        elif self.ext == "html":
            # For HTML, value must be a string; save as-is (sanitization happens during comparison)
            if not isinstance(value, str):
                raise RuntimeError(f"HTML extension requires string value, got {type(value).__name__}")
            with open(received_path, "w", encoding="utf-8") as file:
                file.write(value)
                file.flush()
        elif self.ext == "png":
            # For PNG, value must be bytes; save as-is (pixel hash comparison happens during verification)
            if not isinstance(value, bytes):
                raise RuntimeError(f"PNG extension requires bytes value, got {type(value).__name__}")
            with open(received_path, "wb") as file:
                file.write(value)
                file.flush()
        else:
            # Should not be reached here because of a previous check in __init__
            self._error_extension_not_supported(self.ext)

        # Return self for method call chaining
        return self

    @classmethod
    def verify_all(cls, *, silent: bool = False) -> bool:
        """
        Verify for all guards in this test that '{prefix}.received.ext' is the same as '{prefix}.expected.ext'.
        Defaults to silent=True (no exception) to permit other tests to proceed.

        Notes:
            - If '{prefix}.expected.ext' does not exist, create from '{prefix}.received.ext'
            - If files are the same, delete '{prefix}.received.ext' and '{prefix}.diff.ext'
            - If files differ, write '{prefix}.diff.ext' and raise exception unless silent=True

        Returns:
            bool: True if verification succeeds and false otherwise

        Args:
            silent: If true, do not raise exception and only write the '{prefix}.diff.ext' file
        """
        # Get inner dictionary using output_dir
        output_dir = QaUtil.get_test_dir_from_call_stack()
        inner_dict = cls._guard_dict[output_dir]

        # Skip the delegated guards
        inner_dict = {k: v for k, v in inner_dict.items() if v._delegate_to is None}

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
        Verify for this regression guard that '{prefix}.received.ext' is the same as '{prefix}.expected.ext'.
        Defaults to silent=True (no exception) to permit other tests to proceed.

        Notes:
            - If use_hash=True, uses SHA256 hash comparison storing only hash files
            - If '{prefix}.expected.ext' does not exist, create from '{prefix}.received.ext'
            - If files are the same, delete '{prefix}.received.ext' and '{prefix}.diff.ext'
            - If files differ, write '{prefix}.diff.ext' and raise exception unless silent=True

        Returns:
            bool: True if verification succeeds and false otherwise

        Args:
            silent: If true, do not raise exception and only write the '{prefix}.diff.ext' file
        """
        self.check_frozen()

        # Delegate to a previously created guard with the same output_dir if exists
        if self._delegate_to is not None:
            return self._delegate_to.verify(silent=silent)

        if self._verified:
            # Already verified
            if not silent:
                # Use the existing exception text to raise if silent=False
                raise RuntimeError(self._exception_text)
            else:
                # Otherwise return True if exception text is None (it is set on verification failure)
                return self._exception_text is None

        # Dispatch to hash-based or content-based verification
        if self.use_hash:
            return self._verify_with_hash(silent=silent)
        else:
            return self._verify_with_content(silent=silent)

    def _read_and_sanitize(self, file_path: str) -> str:
        """
        Read file content and apply sanitization for stable comparison.

        Returns:
            Content suitable for comparison (sanitized for HTML with Plotly, pixel hash for PNG, etc.)
        """
        if self.ext == "png":
            return PngUtil.get_pixel_hash_from_png(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if self.ext == "html" and self._is_plotly_html(content):
                content = self._sanitize_plotly_html(content)
            return content

    def _verify_with_content(self, *, silent: bool = False) -> bool:
        """Verify by comparing full file content."""

        received_path = self._get_file_path("received")
        expected_path = self._get_file_path("expected")
        diff_path = self._get_file_path("diff")

        # If received file does not yet exist, return True
        if not os.path.exists(received_path):
            # Do not set the _verified flag so that verification can be performed again at a later time
            return True

        if os.path.exists(expected_path):

            # For PNG files, use pixel hash comparison
            if self.ext == "png":
                from cl.runtime.qa.png_util import PngUtil

                received_hash = PngUtil.get_pixel_hash_from_png(received_path)
                expected_hash = PngUtil.get_pixel_hash_from_png(expected_path)
                content_matches = received_hash == expected_hash
            else:
                # Read both files as text
                with open(received_path, "r", encoding="utf-8") as received_file:
                    received_content = received_file.read()
                with open(expected_path, "r", encoding="utf-8") as expected_file:
                    expected_content = expected_file.read()

                # For HTML files with Plotly content, sanitize in memory for comparison
                if self.ext == "html" and self._is_plotly_html(received_content):
                    received_for_comparison = self._sanitize_plotly_html(received_content)
                    expected_for_comparison = self._sanitize_plotly_html(expected_content)
                else:
                    received_for_comparison = received_content
                    expected_for_comparison = expected_content

                content_matches = received_for_comparison == expected_for_comparison

            # Compare
            if content_matches:
                # Content matches (after sanitization), delete the received file and diff file
                os.remove(received_path)
                if os.path.exists(diff_path):
                    os.remove(diff_path)

                # Return True to indicate verification has been successful
                return True
            else:
                # Content differs
                if self.ext == "png":
                    # For PNG, write pixel hash comparison to diff file
                    diff_content = (
                        f"PNG pixel hash mismatch:\n" f"  Expected: {expected_hash}\n" f"  Received: {received_hash}\n"
                    )
                    with open(diff_path, "w", encoding="utf-8") as diff_file:
                        diff_file.write(diff_content)

                    exception_text = (
                        f"\nPNG regression test failed.\n"
                        f"  Expected pixel hash: {expected_hash}\n"
                        f"  Received pixel hash: {received_hash}\n"
                        f"  Expected file: {expected_path}\n"
                        f"  Received file: {received_path}\n"
                    )
                else:
                    # Generate unified diff for text formats (use sanitized content for HTML)
                    received_lines = received_for_comparison.splitlines(keepends=True)
                    expected_lines = expected_for_comparison.splitlines(keepends=True)

                    # Convert to list first because the returned object is a generator but
                    # we will need to iterate over the lines more than once
                    diff = list(
                        difflib.unified_diff(
                            expected_lines, received_lines, fromfile=expected_path, tofile=received_path, n=0
                        )
                    )

                    # Write the complete unified diff into to the diff file
                    with open(diff_path, "w", encoding="utf-8") as diff_file:
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
                self._exception_text = exception_text

                # Set the _verified flag so that verification returns the same result if attempted again
                # This will prevent further writes to this prefix and extension
                self._verified = True

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

            # Set the _verified flag so that verification returns the same result if attempted again
            # This will prevent further writes to this prefix and extension
            self._verified = True

            # Verification is considered successful if expected file has been created
            return True

    def _verify_with_hash(self, *, silent: bool = False) -> bool:
        """Verify using SHA256 hash comparison, storing only hash files instead of expected/received files."""

        received_path = self._get_file_path("received")
        expected_hash_path = self._get_hash_file_path("expected")
        received_hash_path = self._get_hash_file_path("received")
        diff_hash_path = self._get_hash_file_path("diff")

        # If received file does not yet exist, return True
        if not os.path.exists(received_path):
            # Do not set the _verified flag so that verification can be performed again at a later time
            return True

        # Read and sanitize content, then compute hash
        received_content = self._read_and_sanitize(received_path)
        received_hash = hashlib.sha256(received_content.encode("utf-8")).hexdigest()

        if os.path.exists(expected_hash_path):
            # Read expected hash
            with open(expected_hash_path, "r", encoding="utf-8") as f:
                expected_hash = f.read().strip()

            if received_hash == expected_hash:
                # Hashes match, delete received file and hash files
                os.remove(received_path)
                if os.path.exists(received_hash_path):
                    os.remove(received_hash_path)
                if os.path.exists(diff_hash_path):
                    os.remove(diff_hash_path)

                # Return True to indicate verification has been successful
                return True
            else:
                # Hashes differ, write received hash and diff
                with open(received_hash_path, "w", encoding="utf-8") as f:
                    f.write(received_hash)

                diff_content = f"SHA256 hash mismatch:\n  Expected: {expected_hash}\n  Received: {received_hash}\n"
                with open(diff_hash_path, "w", encoding="utf-8") as f:
                    f.write(diff_content)

                exception_text = (
                    f"\nSHA256 hash regression test failed.\n"
                    f"  Expected hash: {expected_hash}\n"
                    f"  Received hash: {received_hash}\n"
                    f"  Expected hash file: {expected_hash_path}\n"
                    f"  Received hash file: {received_hash_path}\n"
                    f"  Received full file: {received_path}\n"
                )

                # Record into the object even if silent
                self._exception_text = exception_text

                # Set the _verified flag so that verification returns the same result if attempted again
                # This will prevent further writes to this prefix and extension
                self._verified = True

                if not silent:
                    # Raise exception only when not silent
                    raise RuntimeError(exception_text)
                else:
                    return False
        else:
            # Expected hash file does not exist, create it from the received file hash
            with open(expected_hash_path, "w", encoding="utf-8") as f:
                f.write(received_hash)

            # Delete the received file and hash files
            os.remove(received_path)
            if os.path.exists(received_hash_path):
                os.remove(received_hash_path)
            if os.path.exists(diff_hash_path):
                os.remove(diff_hash_path)

            # Set the _verified flag so that verification returns the same result if attempted again
            # This will prevent further writes to this prefix and extension
            self._verified = True

            # Verification is considered successful if expected hash file has been created
            return True

    def _format_txt(self, value: Any) -> str:
        """Format text for regression testing."""

        # Convert to one of the supported output types
        if is_record_type(type(value)) or value.__class__ in SEQUENCE_TYPES or value.__class__ in MAPPING_TYPES:
            value = _YAML_SERIALIZER.serialize(value)
        elif is_key_type(type(value)):
            value = _KEY_SERIALIZER.serialize(value)

        value_type = type(value)
        if value_type in primitive_types:
            # TODO: Use specialized conversion for primitive types
            return str(value) + "\n"
        elif value_type == dict:
            result = _YAML_SERIALIZER.serialize(value) + "\n"
            return result
        elif issubclass(value_type, Enum):
            return str(value.name)
        elif hasattr(value_type, "__iter__"):
            return "\n".join(map(self._format_txt, value)) + "\n"
        else:
            raise RuntimeError(
                f"Argument type {value_type} is not accepted for file extension '{self.ext}'. "
                f"Valid arguments are primitive types, dict, or their iterable."
            )

    def _get_exception_text(self) -> str | None:
        """Get exception text from this guard or the guard it delegates to."""
        if self._delegate_to is not None:
            # Get from the guard this guard delegates to
            return self._delegate_to._get_exception_text()
        else:
            # Get from this guard
            return self._exception_text

    def _get_file_path(self, file_type: str) -> str:
        """The diff between received and expected is written to '{prefix}.diff.ext' located next to the unit test."""
        if file_type not in (file_types := ["received", "expected", "diff"]):
            raise RuntimeError(f"Unknown file type {file_type}, supported types are: {', '.join(file_types)}")
        result = f"{self._output_dir_and_prefix}{file_type}.{self.ext}"
        return result

    def _get_hash_file_path(self, file_type: str) -> str:
        """Get path for hash file: '{prefix}.{file_type}.sha256' located next to the unit test."""
        if file_type not in (file_types := ["received", "expected", "diff"]):
            raise RuntimeError(f"Unknown file type {file_type}, supported types are: {', '.join(file_types)}")
        result = f"{self._output_dir_and_prefix}{file_type}.sha256"
        return result

    @classmethod
    def _is_plotly_html(cls, html: str) -> bool:
        """Check if HTML content was generated by Plotly."""
        return "plotly" in html.lower() and ("cdn.plot.ly" in html or "Plotly.newPlot" in html)

    @classmethod
    def _sanitize_plotly_html(cls, html: str) -> str:
        """Remove version-dependent content from Plotly HTML for stable test comparison."""
        # Replace versioned CDN URL: plotly-X.X.X.min.js -> plotly.min.js
        html = re.sub(r"plotly-[\d.]+\.min\.js", "plotly.min.js", html)
        # Remove integrity hash (changes with version)
        html = re.sub(r'\s+integrity="[^"]*"', "", html)
        # Remove lowercase GUIDs (e.g., 1d6cd542-2bef-4533-9d0b-40e9723ce8f5)
        html = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "", html)
        return html

    @classmethod
    def _error_extension_not_supported(cls, ext: str) -> Any:
        raise RuntimeError(
            f"Extension {ext} is not supported by RegressionGuard. "
            f"Supported extensions: {', '.join(_supported_extensions)}"
        )
