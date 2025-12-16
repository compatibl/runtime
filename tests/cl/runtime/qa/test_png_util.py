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

import io
import pytest
from matplotlib import pyplot as plt

from cl.runtime.qa.png_util import PngUtil
from cl.runtime.plots.matplotlib_util import MatplotlibUtil


class TestPngUtil:
    """Test suite for PNG comparison utilities."""

    def test_same_figure_different_saves(self):
        """Test that the same figure saved twice produces identical checksums when metadata is excluded."""
        # Create a simple figure
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_title("Test Plot")

        # Save to BytesIO twice
        buf1 = io.BytesIO()
        fig.savefig(buf1, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png1 = buf1.getvalue()

        buf2 = io.BytesIO()
        fig.savefig(buf2, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png2 = buf2.getvalue()

        plt.close(fig)

        # Compare with metadata excluded
        result = PngUtil.compare_png_bytes(png1, png2, exclude_metadata=True)

        assert result['match'], f"Checksums don't match: {result['hash1']} vs {result['hash2']}"
        print(f"✓ Checksums match: {result['hash1']}")

    def test_different_metadata_same_image(self):
        """Test that images with different metadata but same visual content match when metadata is excluded."""
        # Create a simple figure
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        # Save with empty metadata
        buf1 = io.BytesIO()
        fig.savefig(buf1, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png1 = buf1.getvalue()

        # Save with different metadata
        buf2 = io.BytesIO()
        fig.savefig(buf2, format='png', metadata={'Title': 'Test', 'Author': 'TestUser'}, dpi=100)
        png2 = buf2.getvalue()

        plt.close(fig)

        # Should NOT match with metadata included
        result_with_metadata = PngUtil.compare_png_bytes(png1, png2, exclude_metadata=False)
        assert not result_with_metadata['match'], "Images should differ when metadata is included"

        # SHOULD match with metadata excluded
        result_without_metadata = PngUtil.compare_png_bytes(png1, png2, exclude_metadata=True)
        assert result_without_metadata['match'], \
            f"Images should match when metadata is excluded: {result_without_metadata['hash1']} vs {result_without_metadata['hash2']}"

        print(f"✓ With metadata: {result_with_metadata['hash1']} != {result_with_metadata['hash2']}")
        print(f"✓ Without metadata: {result_without_metadata['hash1']} == {result_without_metadata['hash2']}")

    def test_different_images(self):
        """Test that actually different images produce different checksums."""
        # Create first figure
        fig1, ax1 = plt.subplots()
        ax1.plot([1, 2, 3], [1, 4, 9])
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png1 = buf1.getvalue()
        plt.close(fig1)

        # Create different figure
        fig2, ax2 = plt.subplots()
        ax2.plot([1, 2, 3], [1, 2, 3])  # Different data
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png2 = buf2.getvalue()
        plt.close(fig2)

        # Compare
        result = PngUtil.compare_png_bytes(png1, png2, exclude_metadata=True)

        assert not result['match'], "Different images should not match"
        print(f"✓ Different images have different checksums: {result['hash1']} != {result['hash2']}")

    def test_checksum_calculation(self):
        """Test standalone checksum calculation."""
        # Create a figure
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        buf = io.BytesIO()
        fig.savefig(buf, format='png', metadata=MatplotlibUtil.no_png_metadata(), dpi=100)
        png_data = buf.getvalue()
        plt.close(fig)

        # Calculate checksum
        checksum = PngUtil.get_png_checksum(png_data, exclude_metadata=True)

        assert len(checksum) == 32, "MD5 checksum should be 32 characters"
        assert checksum.isalnum(), "Checksum should be alphanumeric"
        print(f"✓ Checksum calculated: {checksum}")


if __name__ == "__main__":
    pytest.main(__file__)

