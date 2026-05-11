# coding: utf-8
"""
Tests cho CP10 pack.yml manifest.

Test coverage:
- Pack.yml ton tai
- Capabilities_provided dong bo voi taxonomy.yml
- Deps, error_codes, metadata dung

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from unittest import TestCase
import yaml


class TestCP10Pack(TestCase):
    """Tests cho CP10 pack.yml."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.pack_path = Path("midicoder/emitters/core/search/pack.yml")
        self.taxonomy_path = Path("industry/taxonomy.yml")

    def test_pack_yml_exists(self):
        """Pack.yml phai ton tai."""
        self.assertTrue(
            self.pack_path.exists(),
            "Pack.yml khong ton tai tai midicoder/emitters/core/search/pack.yml",
        )

    def test_pack_yml_has_required_fields(self):
        """Pack.yml co cac fields bat buoc."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        pack = data.get("pack", {})
        self.assertIn("id", pack)
        self.assertIn("capabilities_provided", pack)
        self.assertIn("depends_on", pack)

    def test_pack_capabilities_match_taxonomy(self):
        """Capabilities trong pack.yml phai dong bo voi taxonomy.yml."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            pack_data = yaml.safe_load(f)
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            taxonomy_data = yaml.safe_load(f)

        pack_capabilities = set(
            pack_data.get("pack", {}).get("capabilities_provided", [])
        )

        # Tim CP10 trong taxonomy
        cp10 = None
        for pack in taxonomy_data.get("core_packs", []):
            if pack.get("id") == "CP10":
                cp10 = pack
                break

        self.assertIsNotNone(cp10, "CP10 khong tim thay trong taxonomy.yml")
        taxonomy_capabilities = set(
            cp10.get("capabilities_provided", [])
        )

        self.assertEqual(
            pack_capabilities,
            taxonomy_capabilities,
            f"Capabilities khong giong: pack={pack_capabilities}, "
            f"taxonomy={taxonomy_capabilities}",
        )

    def test_pack_id_is_cp10(self):
        """Pack id phai la CP10."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.assertEqual(data.get("pack", {}).get("id"), "CP10")

    def test_pack_has_correct_capabilities(self):
        """Pack co dung 3 capabilities: search_index, search_query, fulltext_search."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        capabilities = data.get("pack", {}).get("capabilities_provided", [])
        expected = {"search_index", "search_query", "fulltext_search"}
        self.assertEqual(set(capabilities), expected)

    def test_pack_depends_on_cp01_and_cp08(self):
        """Pack depends_on phai chua CP01 va CP08."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        depends = data.get("pack", {}).get("depends_on", [])
        self.assertIn("CP01", depends)
        self.assertIn("CP08", depends)

    def test_taxonomy_cp10_status_is_developing(self):
        """CP10 status trong taxonomy phai la developing."""
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            taxonomy_data = yaml.safe_load(f)

        cp10 = None
        for pack in taxonomy_data.get("core_packs", []):
            if pack.get("id") == "CP10":
                cp10 = pack
                break

        self.assertIsNotNone(cp10)
        self.assertEqual(cp10.get("status"), "developing")


# Run tests
if __name__ == "__main__":
    import unittest

    unittest.main()