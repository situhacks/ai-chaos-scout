"""Tests for the Stage-3 report renderer.

Loads the sample fixture via load_model_from_json, renders all three artifacts,
and validates structural requirements. Stdlib unittest only.
"""

from __future__ import annotations

import email
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scout.render_report import (  # noqa: E402
    ReportModel,
    load_model_from_json,
    render_all,
    render_eml,
    render_html,
    render_markdown,
)

SAMPLE_JSON = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runs", "sample", "report.json",
)


class TestLoadModel(unittest.TestCase):
    def test_load_model_from_json(self):
        model = load_model_from_json(SAMPLE_JSON)
        self.assertIsInstance(model, ReportModel)
        self.assertEqual(model.subject_name, "Meridian Analytics")
        self.assertEqual(model.date, "2026-07-04")
        self.assertTrue(len(model.recommendations) >= 5)
        self.assertTrue(len(model.digest_themes) >= 3)

    def test_recommendation_codes(self):
        model = load_model_from_json(SAMPLE_JSON)
        codes = [r.code for r in model.recommendations]
        self.assertIn("[A1]", codes)
        self.assertIn("[A2]", codes)
        self.assertIn("[A3]", codes)
        self.assertIn("[B1]", codes)
        self.assertIn("[B2]", codes)

    def test_track_distribution(self):
        model = load_model_from_json(SAMPLE_JSON)
        track_a = [r for r in model.recommendations if r.track == "A"]
        track_b = [r for r in model.recommendations if r.track == "B"]
        self.assertTrue(len(track_a) >= 3, "Need >= 3 Track A recs")
        self.assertTrue(len(track_b) >= 2, "Need >= 2 Track B recs")

    def test_disruption_levels_span(self):
        model = load_model_from_json(SAMPLE_JSON)
        levels = {r.disruption for r in model.recommendations}
        self.assertTrue(levels & {1, 2}, "Should have low disruption (Track A)")
        self.assertTrue(levels & {3, 4, 5}, "Should have high disruption (Track B)")


class TestMarkdown(unittest.TestCase):
    def setUp(self):
        self.model = load_model_from_json(SAMPLE_JSON)
        self.md = render_markdown(self.model)

    def test_contains_all_rec_codes(self):
        for rec in self.model.recommendations:
            self.assertIn(rec.code, self.md, f"Missing rec code {rec.code} in markdown")

    def test_contains_tldr(self):
        for bullet in self.model.tldr:
            self.assertIn(bullet, self.md, "TL;DR bullet missing from markdown")

    def test_contains_sections(self):
        self.assertIn("## TL;DR", self.md)
        self.assertIn("## Scoreboard", self.md)
        self.assertIn("Track A", self.md)
        self.assertIn("Track B", self.md)
        self.assertIn("## Deep Dive", self.md)
        self.assertIn("## Provenance", self.md)

    def test_contains_subject_line(self):
        self.assertIn(self.model.subject_line, self.md)

    def test_why_now_links(self):
        for rec in self.model.recommendations:
            for cite in rec.why_now:
                self.assertIn(cite.url, self.md, f"Missing Why-now URL for {rec.code}")

    def test_scoreboard_has_all_recs(self):
        for rec in self.model.recommendations:
            self.assertIn(f"{rec.feasibility}/5", self.md)


class TestHTML(unittest.TestCase):
    def setUp(self):
        self.model = load_model_from_json(SAMPLE_JSON)
        self.html = render_html(self.model)

    def test_self_contained_no_external_assets(self):
        # Source URLs in <a href> are fine; external assets in src= are not.
        import re
        external_srcs = re.findall(r'src\s*=\s*["\']https?://', self.html)
        self.assertEqual(
            len(external_srcs), 0,
            f"HTML must be self-contained, but found external src= refs: {external_srcs}",
        )

    def test_contains_inline_svg(self):
        self.assertIn("<svg", self.html, "HTML must contain inline SVG elements")

    def test_contains_all_rec_codes(self):
        for rec in self.model.recommendations:
            self.assertIn(rec.code, self.html, f"Missing rec code {rec.code} in HTML")

    def test_valid_html_structure(self):
        self.assertIn("<!DOCTYPE html>", self.html)
        self.assertIn("</html>", self.html)
        self.assertIn("<style>", self.html)

    def test_design_tokens_present(self):
        self.assertIn("#F9F7F2", self.html, "Paper background color missing")
        self.assertIn("#1B1F2A", self.html, "Ink color missing")
        self.assertIn("#2438E0", self.html, "Riso blue (Track A) color missing")
        self.assertIn("#EE5340", self.html, "Riso coral (Track B) color missing")

    def test_stage_glyphs_present(self):
        for level in range(1, 6):
            model_recs = [r for r in self.model.recommendations if r.disruption == level]
            if model_recs:
                self.assertIn("<svg", self.html)

    def test_fig_captions(self):
        self.assertIn("Fig. 1", self.html)


class TestEML(unittest.TestCase):
    def setUp(self):
        self.model = load_model_from_json(SAMPLE_JSON)
        self.eml_bytes = render_eml(self.model)

    def test_parses_as_email(self):
        msg = email.message_from_bytes(self.eml_bytes)
        self.assertIsNotNone(msg)

    def test_has_subject(self):
        msg = email.message_from_bytes(self.eml_bytes)
        subject = msg["Subject"]
        self.assertIsNotNone(subject, "EML must have a Subject header")
        self.assertIn("Meridian", subject)

    def test_has_html_part(self):
        msg = email.message_from_bytes(self.eml_bytes)
        html_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    html_parts.append(part.get_payload(decode=True))
        else:
            if msg.get_content_type() == "text/html":
                html_parts.append(msg.get_payload(decode=True))
        self.assertTrue(len(html_parts) > 0, "EML must contain an HTML part")

    def test_no_svg_in_email_html(self):
        msg = email.message_from_bytes(self.eml_bytes)
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                self.assertNotIn(
                    "<svg", html_content,
                    "Email HTML must NOT contain SVG (Outlook Word engine limitation)",
                )

    def test_has_from_header(self):
        msg = email.message_from_bytes(self.eml_bytes)
        self.assertIsNotNone(msg["From"])

    def test_outlook_safe_width(self):
        msg = email.message_from_bytes(self.eml_bytes)
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                self.assertIn("600", html_content, "Email should use 600px layout")

    def test_system_font_stack(self):
        msg = email.message_from_bytes(self.eml_bytes)
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode("utf-8", errors="replace")
                self.assertIn("Segoe UI", html_content)


class TestRenderAll(unittest.TestCase):
    def test_render_all_writes_files(self):
        model = load_model_from_json(SAMPLE_JSON)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_all(model, tmpdir)
            self.assertIn("md", paths)
            self.assertIn("html", paths)
            self.assertIn("eml", paths)
            for kind, path in paths.items():
                self.assertTrue(
                    os.path.exists(path),
                    f"{kind} file was not created at {path}",
                )
                self.assertTrue(
                    os.path.getsize(path) > 0,
                    f"{kind} file is empty at {path}",
                )

    def test_filenames_contain_date(self):
        model = load_model_from_json(SAMPLE_JSON)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = render_all(model, tmpdir)
            for path in paths.values():
                self.assertIn(model.date, os.path.basename(path))


if __name__ == "__main__":
    unittest.main()
