from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from affiliate_friction_auditor.url_utils import (
    canonical_url,
    deep_decode,
    host_of,
    normalize_url,
    path_of,
    query_keys,
    slug_of,
)


class DeepDecodeTests(unittest.TestCase):
    def test_decodes_html_and_percent_encoding(self):
        self.assertEqual(
            deep_decode("https%3A%2F%2Fexample.com%2Fa%3Fx%3D1&amp;y=2"),
            "https://example.com/a?x=1&y=2",
        )

    def test_empty_value(self):
        self.assertEqual(deep_decode(""), "")


class NormalizeUrlTests(unittest.TestCase):
    BASE = "https://example.com/category/page"

    def test_relative_url_and_fragment(self):
        self.assertEqual(
            normalize_url(self.BASE, "../offer#details"),
            "https://example.com/offer",
        )

    def test_protocol_relative_url(self):
        self.assertEqual(
            normalize_url(self.BASE, "//merchant.test/deal/"),
            "https://merchant.test/deal",
        )

    def test_blocks_non_http_schemes_and_fragments(self):
        for value in ("mailto:a@example.com", "tel:+34123", "javascript:void(0)", "data:text/plain,x", "#top"):
            with self.subTest(value=value):
                self.assertEqual(normalize_url(self.BASE, value), "")

    def test_keeps_query_and_removes_trailing_slash(self):
        self.assertEqual(
            normalize_url(self.BASE, "/offer/?tag=abc"),
            "https://example.com/offer/?tag=abc",
        )


class ParsedUrlTests(unittest.TestCase):
    def test_canonical_url_removes_fragment_and_trailing_slash(self):
        self.assertEqual(
            canonical_url(" https://Example.com/A/?x=1#frag "),
            "https://Example.com/A/?x=1",
        )

    def test_host_is_lowercase(self):
        self.assertEqual(host_of("https://WWW.Example.COM/path"), "www.example.com")

    def test_host_can_decode_encoded_url(self):
        self.assertEqual(
            host_of("https%3A%2F%2Fexample.com%2Foffer", decode=True),
            "example.com",
        )

    def test_path_is_lowercase_and_root_safe(self):
        self.assertEqual(path_of("https://example.com/Some/Path/"), "/some/path")
        self.assertEqual(path_of("https://example.com"), "/")

    def test_query_keys_are_lowercase(self):
        self.assertEqual(
            query_keys("https://example.com/?TAG=abc&utm_source=x&empty="),
            {"tag", "utm_source"},
        )

    def test_slug_uses_last_path_component(self):
        self.assertEqual(slug_of("https://example.com/category/Product-123/"), "product-123")
        self.assertEqual(slug_of("https://example.com"), "")


if __name__ == "__main__":
    unittest.main()
