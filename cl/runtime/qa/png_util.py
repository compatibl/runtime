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

import hashlib
import struct
from io import BytesIO
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image


class PngUtil:
    """Utility for comparing PNG images byte-by-byte while excluding metadata chunks."""

    # PNG chunk types that contain metadata (should be excluded from comparison)
    METADATA_CHUNKS = {
        b"tEXt",  # Textual data
        b"zTXt",  # Compressed textual data
        b"iTXt",  # International textual data
        b"tIME",  # Last modification time
        b"pHYs",  # Physical pixel dimensions
        b"sPLT",  # Suggested palette
        b"iCCP",  # ICC color profile
        b"sRGB",  # Standard RGB color space
        b"sBIT",  # Significant bits
        b"gAMA",  # Image gamma
        b"cHRM",  # Primary chromaticities
        b"eXIf",  # Exif metadata
    }

    # Critical chunks that define the actual image data (must be preserved)
    CRITICAL_CHUNKS = {
        b"IHDR",  # Image header
        b"PLTE",  # Palette
        b"IDAT",  # Image data
        b"IEND",  # Image end
    }

    @staticmethod
    def get_png_bytes_from_figure(fig, dpi: int = 100, bbox_inches: str = "tight", pad_inches: float = 0.1) -> bytes:
        """
        Get PNG bytes from a matplotlib figure.

        Args:
            fig: Matplotlib figure object
            dpi: DPI for rendering (default: 100)
            bbox_inches: Bounding box setting (default: "tight")
            pad_inches: Padding in inches (default: 0.1)

        Returns:
            bytes: PNG image data
        """

        # Render figure to BytesIO buffer
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=dpi, bbox_inches=bbox_inches, pad_inches=pad_inches, transparent=False)
        png_bytes = buffer.getvalue()
        buffer.close()

        return png_bytes

    @staticmethod
    def get_pixel_hash_from_figure(fig, dpi: int = 100, bbox_inches: str = "tight", pad_inches: float = 0.1) -> str:
        """
        Get MD5 hash of pixel data from a matplotlib figure.

        Args:
            fig: Matplotlib figure object
            dpi: DPI for rendering (default: 100)
            bbox_inches: Bounding box setting (default: "tight")
            pad_inches: Padding in inches (default: 0.1)

        Returns:
            str: MD5 hash of the pixel array
        """

        # Render figure to BytesIO buffer
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=dpi, bbox_inches=bbox_inches, pad_inches=pad_inches, transparent=False)
        buffer.seek(0)

        # Load as pixel array
        with Image.open(buffer) as img:
            img_rgba = img.convert("RGBA")
            arr = np.array(img_rgba, dtype=np.uint8)

        buffer.close()

        # Calculate MD5 hash of pixel data
        return hashlib.md5(arr.tobytes()).hexdigest()

    @staticmethod
    def get_pixel_hash_from_png(png_source: str | BytesIO) -> str:
        """
        Get MD5 hash of pixel data from a PNG file or BytesIO object.

        Args:
            png_source: PNG file path or BytesIO object

        Returns:
            str: MD5 hash of the pixel array
        """

        # Load as pixel array
        with Image.open(png_source) as img:
            img_rgba = img.convert("RGBA")
            arr = np.array(img_rgba, dtype=np.uint8)

        # Calculate MD5 hash of pixel data
        return hashlib.md5(arr.tobytes()).hexdigest()

    @staticmethod
    def compare_pixel_data(file1: str | BytesIO, file2: str | BytesIO) -> dict[str, Any]:
        """
        Compare actual pixel data of two PNG files, ignoring compression/encoding differences.

        Args:
            file1: First PNG file path or BytesIO object
            file2: Second PNG file path or BytesIO object

        Returns:
            Dictionary with comparison results:
            - 'match': True if pixel data is identical
            - 'pixel_hash1': MD5 hash of first image's pixel array
            - 'pixel_hash2': MD5 hash of second image's pixel array
            - 'shape1': Shape of first image array
            - 'shape2': Shape of second image array
        """

        # Load images as pixel arrays
        with Image.open(file1) as img1:
            img1_rgba = img1.convert("RGBA")
            arr1 = np.array(img1_rgba, dtype=np.uint8)

        with Image.open(file2) as img2:
            img2_rgba = img2.convert("RGBA")
            arr2 = np.array(img2_rgba, dtype=np.uint8)

        # Calculate MD5 hash of pixel data
        hash1 = hashlib.md5(arr1.tobytes()).hexdigest()
        hash2 = hashlib.md5(arr2.tobytes()).hexdigest()

        return {
            "match": hash1 == hash2,
            "pixel_hash1": hash1,
            "pixel_hash2": hash2,
            "shape1": arr1.shape,
            "shape2": arr2.shape,
        }

    @classmethod
    def extract_png_data_chunks(cls, png_bytes: bytes) -> bytes:
        """
        Extract only the data-relevant chunks from a PNG file, excluding metadata.

        Args:
            png_bytes: Raw bytes of a PNG file

        Returns:
            bytes: PNG file with only critical and ancillary data chunks (no metadata)
        """
        # Verify PNG signature
        if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG signature")

        # Start with PNG signature
        result = bytearray(png_bytes[:8])

        # Parse chunks
        offset = 8
        while offset < len(png_bytes):
            # Read chunk length (4 bytes, big-endian)
            if offset + 4 > len(png_bytes):
                break
            chunk_length = struct.unpack(">I", png_bytes[offset : offset + 4])[0]
            offset += 4

            # Read chunk type (4 bytes)
            if offset + 4 > len(png_bytes):
                break
            chunk_type = png_bytes[offset : offset + 4]
            offset += 4

            # Read chunk data
            if offset + chunk_length > len(png_bytes):
                break
            chunk_data = png_bytes[offset : offset + chunk_length]
            offset += chunk_length

            # Read CRC (4 bytes)
            if offset + 4 > len(png_bytes):
                break
            chunk_crc = png_bytes[offset : offset + 4]
            offset += 4

            # Include chunk if it's not metadata
            if chunk_type not in cls.METADATA_CHUNKS:
                # Write chunk length
                result.extend(struct.pack(">I", chunk_length))
                # Write chunk type
                result.extend(chunk_type)
                # Write chunk data
                result.extend(chunk_data)
                # Write CRC
                result.extend(chunk_crc)

            # Stop at IEND chunk
            if chunk_type == b"IEND":
                break

        return bytes(result)

    @classmethod
    def compare_png_bytes(cls, png1: bytes, png2: bytes, exclude_metadata: bool = True) -> dict:
        """
        Compare two PNG images byte-by-byte.

        Args:
            png1: Bytes of the first PNG image
            png2: Bytes of the second PNG image
            exclude_metadata: If True, exclude metadata chunks from comparison

        Returns:
            dict: Comparison result with keys:
                - 'match': bool indicating if images match
                - 'hash1': MD5 hash of first image
                - 'hash2': MD5 hash of second image
                - 'size1': Size in bytes of first image (after filtering)
                - 'size2': Size in bytes of second image (after filtering)
        """
        # Extract data chunks if excluding metadata
        if exclude_metadata:
            data1 = cls.extract_png_data_chunks(png1)
            data2 = cls.extract_png_data_chunks(png2)
        else:
            data1 = png1
            data2 = png2

        # Calculate hashes
        hash1 = hashlib.md5(data1).hexdigest()
        hash2 = hashlib.md5(data2).hexdigest()

        return {
            "match": hash1 == hash2,
            "hash1": hash1,
            "hash2": hash2,
            "size1": len(data1),
            "size2": len(data2),
        }

    @classmethod
    def compare_png_files(cls, file1: str | Path, file2: str | Path, exclude_metadata: bool = True) -> dict:
        """
        Compare two PNG files byte-by-byte.

        Args:
            file1: Path to the first PNG file
            file2: Path to the second PNG file
            exclude_metadata: If True, exclude metadata chunks from comparison

        Returns:
            dict: Comparison result (see compare_png_bytes for details)
        """
        with open(file1, "rb") as f1:
            png1 = f1.read()

        with open(file2, "rb") as f2:
            png2 = f2.read()

        return cls.compare_png_bytes(png1, png2, exclude_metadata)

    @classmethod
    def get_png_checksum(cls, png_data: bytes, exclude_metadata: bool = True) -> str:
        """
        Calculate MD5 checksum of a PNG image.

        Args:
            png_data: Bytes of the PNG image
            exclude_metadata: If True, exclude metadata chunks from checksum calculation

        Returns:
            str: Hexadecimal MD5 checksum
        """
        if exclude_metadata:
            png_data = cls.extract_png_data_chunks(png_data)

        return hashlib.md5(png_data).hexdigest()

    @classmethod
    def get_png_file_checksum(cls, file_path: str | Path, exclude_metadata: bool = True) -> str:
        """
        Calculate MD5 checksum of a PNG file.

        Args:
            file_path: Path to the PNG file
            exclude_metadata: If True, exclude metadata chunks from checksum calculation

        Returns:
            str: Hexadecimal MD5 checksum
        """
        with open(file_path, "rb") as f:
            png_data = f.read()

        return cls.get_png_checksum(png_data, exclude_metadata)

    @classmethod
    def save_png_without_metadata(cls, input_path: str | Path, output_path: str | Path) -> None:
        """
        Save a PNG file with metadata chunks removed.

        Args:
            input_path: Path to the input PNG file
            output_path: Path to save the output PNG file
        """
        with open(input_path, "rb") as f:
            png_data = f.read()

        filtered_data = cls.extract_png_data_chunks(png_data)

        with open(output_path, "wb") as f:
            f.write(filtered_data)
