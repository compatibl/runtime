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
import os
from dataclasses import dataclass
from PIL import Image
from cl.runtime.view.dag.dag import Dag
from cl.runtime.view.dag.dag_edge import DagEdge
from cl.runtime.view.dag.dag_layout import DagLayout
from cl.runtime.view.dag.dag_node_data import DagNodeData
from cl.runtime.view.dag.nodes.add_text_node import AddTextNode
from cl.runtime.view.dag.nodes.text_input_node import TextInputNode
from cl.runtime.view.dag.nodes.text_output_node import TextOutputNode
from cl.runtime.views.html_view import HtmlView
from cl.runtime.views.pdf_view import PdfView
from cl.runtime.views.png_view import PngView
from cl.runtime.views.script import Script
from cl.runtime.views.script_language import ScriptLanguage
from stubs.cl.runtime.views.stub_viewers import StubViewers


@dataclass(slots=True, kw_only=True)
class StubMediaViewers(StubViewers):
    """Stub viewers for media types (images, files, text, etc.)."""

    def view_png(self) -> PngView:
        """Stub viewer returning a PngView of a simple generated image."""

        # Create a new 300x300 image with RGB mode
        width, height = 100, 100
        sample_image = Image.new("RGB", (width, height))

        # Get pixel access object
        pixels = sample_image.load()

        # Create gradient
        for x in range(width):
            for y in range(height):
                # Calculate color transition
                r = int(103 + (255 - 103) * (x / width))  # Red: 103 to 255
                g = int(255 + (103 - 255) * (x / width))  # Green: 255 to 103
                b = int(255 + (103 - 255) * (x / width))  # Blue: 255 to 103
                pixels[x, y] = (r, g, b)

        # Save to buffer
        png_buffer = io.BytesIO()
        sample_image.save(png_buffer, format="PNG", optimize=True, compress_level=9)

        # Get the PNG image bytes and wrap in PngView
        png_bytes = png_buffer.getvalue()
        return PngView(png_bytes=png_bytes)

    def view_pdf(self) -> PdfView:
        """Stub viewer returning a PdfView of a pdf file."""
        file_path = os.path.join(os.path.dirname(__file__), "stub_media_viewers_pdf_sample.pdf")
        with open(file_path, mode="rb") as file:
            content = file.read()
        return PdfView(pdf_bytes=content)

    def view_html(self) -> HtmlView:
        """Stub viewer returning a HtmlView."""
        title = "HTML Title"
        heading = "HTML Heading"
        paragraph = "Stub text."

        html_content = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body>
            <h1>{heading}</h1>
            <p>{paragraph}</p>
        </body>
        </html>"""

        html_bytes = html_content.encode("utf-8")
        return HtmlView(html_bytes=html_bytes)

    def view_dag(self) -> Dag:
        """Stub viewer returning a DAG."""

        # TODO: Switch to the new DAG classes
        dag = Dag(
            name="dag_data",
            nodes=[
                TextInputNode(id_="root", text="root", data=DagNodeData(label="Input")),
                AddTextNode(id_="a", text_to_add="add A", data=DagNodeData(label="A")),
                AddTextNode(id_="b", text_to_add="add B", data=DagNodeData(label="B")),
                AddTextNode(id_="c", text_to_add="add C", data=DagNodeData(label="C")),
                AddTextNode(id_="d", text_to_add="add D", data=DagNodeData(label="D")),
                AddTextNode(id_="e", text_to_add="add E", data=DagNodeData(label="E")),
                TextOutputNode(id_="output1", data=DagNodeData(label="Output 1")),
                TextOutputNode(id_="output2", data=DagNodeData(label="Output 2")),
            ],
            edges=[
                DagEdge(source="root", target="a", id_="root;a", label="main stream"),
                DagEdge(source="a", target="b", id_="a;b", label="filtered stream"),
                DagEdge(source="a", target="e", id_="a;e", label="main stream"),
                DagEdge(source="e", target="output1", id_="e;output1", label="to text"),
                DagEdge(source="e", target="output2", id_="e;output2", label="to file"),
                DagEdge(source="d", target="output2", id_="d;output2", label="to file"),
                DagEdge(source="d", target="e", id_="d;e"),
                DagEdge(source="c", target="d", id_="c;d"),
                DagEdge(source="b", target="c", id_="b;c"),
            ],
        )

        return Dag.auto_layout_dag(dag, layout_mode=DagLayout.PLANAR, base_scale=180)

    def view_markdown(self) -> Script:
        """Stub viewer returning a Markdown text."""

        return Script(
            name="Stub markdown text.",
            language=ScriptLanguage.MARKDOWN,
            body=[
                "# Test markdown.",
                "",
                "Welcome to this **Markdown** document.",
                "## Introduction",
                "This is a paragraph explaining the purpose of this document.",
                "## Features",
                "",
                "- Easy to read",
                "- Easy to write",
                "- Supports **bold** and *italic* text",
                "- Allows inserting [links](https://example.com)",
                "",
                "### Code Example",
                "",
                "Here is a code snippet:",
                "",
                "```python",
                "def say_hello():",
                "    print('Hello, Markdown!')",
            ],
        )
