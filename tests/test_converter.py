"""Tests for PDF2MD converter."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import pymupdf

from pdf2md.converter import PDFToMarkdownConverter
from pdf2md.cli import main


def create_sample_lecture_pdf(pdf_path: str):
    """Generate a realistic 4-slide lecture presentation PDF for testing."""
    doc = pymupdf.open()

    # Slide 1: Title Slide
    p1 = doc.new_page(width=960, height=540)  # 16:9 aspect ratio
    p1.insert_text(
        (100, 180),
        "Introduction to Algorithms",
        fontsize=36,
        fontname="helv",
    )
    p1.insert_text(
        (100, 240),
        "Lecture 01 - Asymptotic Analysis & Recursion",
        fontsize=20,
        fontname="helv",
    )
    p1.insert_text(
        (100, 320),
        "Instructor: Dr. Alan Turing\nDepartment of Computer Science\nSpring Semester 2024",
        fontsize=14,
        fontname="helv",
    )

    # Slide 2: Hierarchy & Bullet Points with recurring footer
    p2 = doc.new_page(width=960, height=540)
    p2.insert_text((80, 80), "What is an Algorithm?", fontsize=28, fontname="helv")
    p2.insert_text((80, 150), "• A well-defined computational procedure", fontsize=16, fontname="helv")
    p2.insert_text((110, 185), "• Takes some value or set of values as input", fontsize=14, fontname="helv")
    p2.insert_text((110, 215), "• Produces some value or set of values as output", fontsize=14, fontname="helv")
    p2.insert_text((80, 260), "• Key Properties:", fontsize=16, fontname="helv")
    p2.insert_text((110, 295), "1. Correctness", fontsize=14, fontname="helv")
    p2.insert_text((110, 325), "2. Efficiency (Time and Space)", fontsize=14, fontname="helv")
    p2.insert_text((110, 355), "3. Finiteness", fontsize=14, fontname="helv")
    # Recurring footer
    p2.insert_text((80, 500), "CS101 - Algorithms | Spring 2024", fontsize=10, fontname="helv")
    p2.insert_text((850, 500), "Page 2 / 4", fontsize=10, fontname="helv")

    # Slide 3: Two-Column Slide
    p3 = doc.new_page(width=960, height=540)
    p3.insert_text((80, 80), "Divide and Conquer Strategy", fontsize=28, fontname="helv")
    # Left Column
    p3.insert_text((80, 150), "Advantages:", fontsize=18, fontname="helv")
    p3.insert_text((80, 190), "• Solves difficult conceptual problems", fontsize=14, fontname="helv")
    p3.insert_text((80, 220), "• High parallelism potential", fontsize=14, fontname="helv")
    p3.insert_text((80, 250), "• Efficient memory cache usage", fontsize=14, fontname="helv")
    # Right Column
    p3.insert_text((520, 150), "Disadvantages:", fontsize=18, fontname="helv")
    p3.insert_text((520, 190), "• Recursion overhead / stack frames", fontsize=14, fontname="helv")
    p3.insert_text((520, 220), "• Base condition complexity", fontsize=14, fontname="helv")
    p3.insert_text((520, 250), "• May be slower for small N", fontsize=14, fontname="helv")
    # Recurring footer
    p3.insert_text((80, 500), "CS101 - Algorithms | Spring 2024", fontsize=10, fontname="helv")
    p3.insert_text((850, 500), "Page 3 / 4", fontsize=10, fontname="helv")

    # Slide 4: Code block & Note
    p4 = doc.new_page(width=960, height=540)
    p4.insert_text((80, 80), "Binary Search Implementation", fontsize=28, fontname="helv")
    code_text = (
        "def binary_search(arr, target):\n"
        "    low = 0\n"
        "    high = len(arr) - 1\n"
        "    while low <= high:\n"
        "        mid = (low + high) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        elif arr[mid] < target:\n"
        "            low = mid + 1\n"
        "        else:\n"
        "            high = mid - 1\n"
        "    return -1"
    )
    p4.insert_text((80, 140), code_text, fontsize=12, fontname="cour")
    # Recurring footer
    p4.insert_text((80, 500), "CS101 - Algorithms | Spring 2024", fontsize=10, fontname="helv")
    p4.insert_text((850, 500), "Page 4 / 4", fontsize=10, fontname="helv")

    # Add a presenter note annotation on slide 4
    p4.add_text_annot((900, 80), "Remember to explain why (low + high) // 2 might overflow in Java/C++.")

    doc.save(pdf_path)
    doc.close()


class TestPDF2MD(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_pdf = os.path.join(self.temp_dir, "sample_lecture.pdf")
        create_sample_lecture_pdf(self.sample_pdf)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_standard_conversion(self):
        converter = PDFToMarkdownConverter(format_type="standard")
        out_md = os.path.join(self.temp_dir, "output.md")
        result = converter.convert(self.sample_pdf, out_md)

        self.assertEqual(result["total_slides"], 4)
        self.assertTrue(os.path.exists(out_md))

        with open(out_md, "r", encoding="utf-8") as f:
            content = f.read()

        # Check titles
        self.assertIn("Introduction to Algorithms", content)
        self.assertIn("What is an Algorithm?", content)
        self.assertIn("Divide and Conquer Strategy", content)
        self.assertIn("Binary Search Implementation", content)

        # Check code block formatting
        self.assertIn("```", content)
        self.assertIn("def binary_search", content)

        # Check presenter notes
        self.assertIn("Remember to explain why", content)

        # Recurring footer should be filtered out
        self.assertNotIn("CS101 - Algorithms | Spring 2024", content)

    def test_marp_format(self):
        converter = PDFToMarkdownConverter(format_type="marp")
        out_md = os.path.join(self.temp_dir, "marp_output.md")
        converter.convert(self.sample_pdf, out_md)

        with open(out_md, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertTrue(content.startswith("---\nmarp: true"))
        self.assertIn("\n\n---\n\n", content)

    def test_obsidian_format(self):
        converter = PDFToMarkdownConverter(format_type="obsidian")
        out_md = os.path.join(self.temp_dir, "obsidian_output.md")
        converter.convert(self.sample_pdf, out_md)

        with open(out_md, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("tags:", content)
        self.assertIn("lecture-notes", content)
        self.assertIn("> [!note] Presenter Notes", content)

    def test_split_slides(self):
        out_dir = os.path.join(self.temp_dir, "split_output")
        converter = PDFToMarkdownConverter(split_slides=True)
        result = converter.convert(self.sample_pdf, out_dir)

        self.assertTrue(os.path.exists(os.path.join(out_dir, "README.md")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "slides_md", "slide_001.md")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "slides_md", "slide_004.md")))

    def test_render_slides(self):
        out_md = os.path.join(self.temp_dir, "rendered.md")
        converter = PDFToMarkdownConverter(render_slides=True)
        converter.convert(self.sample_pdf, out_md)

        slides_img_dir = os.path.join(self.temp_dir, "slides")
        self.assertTrue(os.path.exists(slides_img_dir))
        self.assertTrue(os.path.exists(os.path.join(slides_img_dir, "slide_001.png")))

        with open(out_md, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("![Slide 1](slides/slide_001.png)", content)

    def test_cli_execution(self):
        out_md = os.path.join(self.temp_dir, "cli_output.md")
        exit_code = main([self.sample_pdf, "-o", out_md, "--quiet"])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.exists(out_md))


if __name__ == "__main__":
    unittest.main()
