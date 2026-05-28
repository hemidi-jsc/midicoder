# coding: utf-8
"""
Tests cho CP10 pack.yml manifest.

Test coverage:
- Pack.yml ton tai tai dung duong dan
- Capabilities_provided dong bo voi taxonomy.yml
- Deps, error_codes, metadata dung
- File contributions co pack_emitter registered
- Pack co cac sections bat buoc (infrastructure, definitions, obligations)

Author: Midicoder Team
Version: 1.0.0
"""

from pathlib import Path
from unittest import TestCase

import yaml


class TestCP10Pack(TestCase):
    """Tests cho CP10 pack.yml."""

    def setUp(self):
        """Thiet lap test fixtures."""
        self.pack_path = Path("midicoder/packs/cp_full_search/pack.yml")
        self.taxonomy_path = Path("industry/taxonomy.yml")

    def _load_pack(self) -> dict:
        """Load pack.yml va tra ve dict."""
        with open(self.pack_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_taxonomy(self) -> dict:
        """Load taxonomy.yml va tra ve dict."""
        with open(self.taxonomy_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_cp10_from_taxonomy(self) -> dict | None:
        """Tim va tra ve CP10 entry trong taxonomy."""
        taxonomy = self._load_taxonomy()
        for pack in taxonomy.get("core_packs", []):
            if pack.get("id") == "CP10":
                return pack
        return None

    # ---- existence ----

    def test_pack_yml_exists(self):
        """Pack.yml phai ton tai tai duong dan cp_full_search."""
        self.assertTrue(
            self.pack_path.exists(),
            "Pack.yml khong ton tai tai midicoder/packs/cp_full_search/pack.yml",
        )

    # ---- required fields ----

    def test_pack_yml_has_required_fields(self):
        """Pack.yml co cac fields bat buoc."""
        data = self._load_pack()
        pack = data.get("pack", {})
        for field in ("id", "name", "internal_id", "version", "status",
                      "capabilities_provided", "depends_on"):
            self.assertIn(field, pack, f"Theo '{field}' trong pack.yml")

    def test_pack_id_is_cp10(self):
        """Pack id phai la CP10."""
        data = self._load_pack()
        self.assertEqual(data["pack"]["id"], "CP10")

    def test_pack_internal_id(self):
        """Pack internal_id phai la cp_full_search."""
        data = self._load_pack()
        self.assertEqual(data["pack"]["internal_id"], "cp_full_search")

    def test_pack_version(self):
        """Pack version phai co dang semver."""
        data = self._load_pack()
        v = data["pack"]["version"]
        parts = v.split(".")
        self.assertEqual(len(parts), 3, "Version phai co 3 phan: major.minor.patch")

    # ---- capabilities ----

    def test_pack_has_all_capabilities(self):
        """Pack co 6 capabilities: search_index, search_query, fulltext_search,
        vector_search, geo_search, faceted_aggregation."""
        data = self._load_pack()
        capabilities = set(data["pack"]["capabilities_provided"])
        expected = {
            "search_index",
            "search_query",
            "fulltext_search",
            "vector_search",
            "geo_search",
            "faceted_aggregation",
        }
        self.assertEqual(capabilities, expected)

    def test_pack_capabilities_match_taxonomy(self):
        """Capabilities trong pack.yml phai dong bo voi taxonomy.yml."""
        data = self._load_pack()
        pack_capabilities = set(data["pack"]["capabilities_provided"])
        cp10 = self._get_cp10_from_taxonomy()
        self.assertIsNotNone(cp10, "CP10 khong tim thay trong taxonomy.yml")
        taxonomy_capabilities = set(cp10["capabilities_provided"])

        self.assertEqual(
            pack_capabilities,
            taxonomy_capabilities,
            f"Capabilities khong giong: pack={pack_capabilities}, "
            f"taxonomy={taxonomy_capabilities}",
        )

    # ---- dependencies ----

    def test_pack_depends_on_cp08(self):
        """Pack depends_on phai chua CP08 (Database)."""
        data = self._load_pack()
        depends = data["pack"]["depends_on"]
        self.assertIn("CP08", depends)

    # ---- error codes ----

    def test_pack_has_error_codes(self):
        """Pack co error_codes voi dung prefix."""
        data = self._load_pack()
        error_codes = data["pack"].get("error_codes", {})
        self.assertEqual(error_codes["prefix"], "MDC-CP10")

    # ---- file contributions ----

    def test_file_contributions_infrastructure_exists(self):
        """Pack phai co file_contributions.infrastructure."""
        data = self._load_pack()
        fc = data["pack"].get("file_contributions", {})
        self.assertIn("infrastructure", fc)
        self.assertTrue(len(fc["infrastructure"]) > 0)

    def test_infrastructure_entries_have_pack_emitter(self):
        """Tat ca infrastructure entries co pack_emitter field."""
        data = self._load_pack()
        for entry in data["pack"]["file_contributions"]["infrastructure"]:
            self.assertIn("pack_emitter", entry)

    def test_infrastructure_entries_have_required_fields(self):
        """Tat ca infrastructure entries co path, file_type, template, stacks."""
        data = self._load_pack()
        for entry in data["pack"]["file_contributions"]["infrastructure"]:
            for field in ("path", "file_type", "template", "stacks"):
                self.assertIn(field, entry, f"Theo '{field}' trong entry: {entry.get('path')}")

    # ---- taxonomy ----

    def test_taxonomy_cp10_exists(self):
        """CP10 phai ton tai trong taxonomy.yml."""
        cp10 = self._get_cp10_from_taxonomy()
        self.assertIsNotNone(cp10)

    def test_taxonomy_cp10_status_is_developing(self):
        """CP10 status trong taxonomy phai la developing."""
        cp10 = self._get_cp10_from_taxonomy()
        self.assertIsNotNone(cp10)
        self.assertEqual(cp10["status"], "developing")

    def test_taxonomy_cp10_internal_id(self):
        """CP10 internal_id trong taxonomy phai la cp_full_search."""
        cp10 = self._get_cp10_from_taxonomy()
        self.assertIsNotNone(cp10)
        self.assertEqual(cp10["internal_id"], "cp_full_search")

    def test_taxonomy_cp10_depends_on_cp08(self):
        """CP10 trong taxonomy phai depend on CP08."""
        cp10 = self._get_cp10_from_taxonomy()
        self.assertIn("CP08", cp10["depends_on"])

    # ---- definitions & obligations ----

    def test_pack_has_definitions(self):
        """Pack phai co definitions."""
        data = self._load_pack()
        defs = data["pack"].get("definitions", [])
        self.assertTrue(len(defs) > 0, "Pack phai co it nhat 1 definition")
        # Moi definition co name va description
        for d in defs:
            self.assertIn("name", d)
            self.assertIn("description", d)

    def test_pack_has_obligations(self):
        """Pack phai co obligations."""
        data = self._load_pack()
        obs = data["pack"].get("obligations", [])
        self.assertTrue(len(obs) > 0, "Pack phai co it nhat 1 obligation")
        for o in obs:
            self.assertIn("name", o)
            self.assertIn("description", o)

    def test_definitions_count_matches(self):
        """definitions_count trong pack.yml phai bang so definitions thuc te."""
        data = self._load_pack()
        pack = data["pack"]
        self.assertEqual(
            pack["definitions_count"],
            len(pack["definitions"]),
            "definitions_count phai bang so definitions",
        )

    def test_obligations_count_matches(self):
        """obligations_count trong pack.yml phai bang so obligations thuc te."""
        data = self._load_pack()
        pack = data["pack"]
        self.assertEqual(
            pack["obligations_count"],
            len(pack["obligations"]),
            "obligations_count phai bang so obligations",
        )


if __name__ == "__main__":
    import unittest
    unittest.main()