"""
Test suite cho DSL v1 Loader Module.

Test coverage cho:
- YAML loading với caching
- ProjectionTree loading từ DSL directory
- Cache invalidation
- Error handling

Mục tiêu coverage: >80%
"""

from pathlib import Path
import tempfile
import shutil
from unittest import TestCase
from unittest.mock import patch, MagicMock

import pytest

from midicoder.dsl.loader import (
    load_yaml,
    load_projection_tree,
    load_yaml_unsafe,
    YAMLCache,
    get_yaml_cache,
    clear_yaml_cache,
    enable_yaml_caching,
    disable_yaml_caching,
    is_yaml_caching_enabled,
)
from midicoder.dsl.projection import (
    NodeKind,
    ProjectionNode,
)


# ============================================================================
# YAMLCache Tests
# ============================================================================


class TestYAMLCache(TestCase):
    """Test YAMLCache functionality."""

    def setUp(self):
        """Setup before each test."""
        self.cache = YAMLCache(max_size=10, default_ttl=300.0)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup after each test."""
        self.cache.invalidate_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_set_and_get(self):
        """Test basic cache set and get."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        data = {"key": "value"}
        self.cache.set(test_file, data)

        cached = self.cache.get(test_file)
        self.assertEqual(cached, data)

    def test_cache_miss_on_nonexistent_file(self):
        """Test cache miss for file not in cache."""
        test_file = Path(self.temp_dir) / "missing.yaml"
        cached = self.cache.get(test_file)
        self.assertIsNone(cached)

    def test_cache_invalidate(self):
        """Test invalidate specific cache entry."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        self.cache.set(test_file, {"data": "value"})
        self.assertTrue(self.cache.invalidate(test_file))

        cached = self.cache.get(test_file)
        self.assertIsNone(cached)

    def test_cache_clear_all(self):
        """Test clear all cache entries."""
        file1 = Path(self.temp_dir) / "test1.yaml"
        file2 = Path(self.temp_dir) / "test2.yaml"
        file1.write_text("test1")
        file2.write_text("test2")

        self.cache.set(file1, {"data": 1})
        self.cache.set(file2, {"data": 2})

        self.assertEqual(self.cache.size, 2)
        self.cache.invalidate_all()
        self.assertEqual(self.cache.size, 0)

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        # First access - miss
        self.cache.get(test_file)

        # Set and access - hit
        self.cache.set(test_file, {"data": "value"})
        self.cache.get(test_file)

        self.assertEqual(self.cache.hit_rate, 0.5)  # 1 hit, 1 miss

    def test_cache_stats(self):
        """Test cache stats property."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        self.cache.set(test_file, {"data": "value"})
        stats = self.cache.stats

        self.assertIn("size", stats)
        self.assertIn("max_size", stats)
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
        self.assertIn("hit_rate", stats)
        self.assertEqual(stats["max_size"], 10)


class TestYAMLCachingFunctions(TestCase):
    """Test global caching functions."""

    def setUp(self):
        """Setup before each test."""
        clear_yaml_cache()
        enable_yaml_caching()

    def tearDown(self):
        """Cleanup after each test."""
        clear_yaml_cache()
        enable_yaml_caching()

    def test_enable_disable_caching(self):
        """Test enable/disable caching functions."""
        self.assertTrue(is_yaml_caching_enabled())

        disable_yaml_caching()
        self.assertFalse(is_yaml_caching_enabled())

        enable_yaml_caching()
        self.assertTrue(is_yaml_caching_enabled())

    def test_get_yaml_cache(self):
        """Test get_yaml_cache returns YAMLCache instance."""
        cache = get_yaml_cache()
        self.assertIsInstance(cache, YAMLCache)

    def test_clear_yaml_cache(self):
        """Test clear_yaml_cache clears all entries."""
        temp_dir = tempfile.mkdtemp()
        try:
            test_file = Path(temp_dir) / "test.yaml"
            test_file.write_text("key: value")

            cache = get_yaml_cache()
            cache.set(test_file, {"data": "value"})

            clear_yaml_cache()
            self.assertEqual(cache.size, 0)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# load_yaml Tests
# ============================================================================


class TestLoadYAML(TestCase):
    """Test load_yaml function."""

    def setUp(self):
        """Setup before each test."""
        self.temp_dir = tempfile.mkdtemp()
        clear_yaml_cache()
        enable_yaml_caching()

    def tearDown(self):
        """Cleanup after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_yaml_cache()
        enable_yaml_caching()

    def test_load_valid_yaml(self):
        """Test loading valid YAML file."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("entities:\n  - id: Order\n    fields: []")

        data, is_cached = load_yaml(test_file)
        self.assertIn("entities", data)
        self.assertEqual(len(data["entities"]), 1)
        self.assertEqual(data["entities"][0]["id"], "Order")

    def test_load_yaml_cache_hit(self):
        """Test YAML cache hit on second load."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        # First load - cache miss
        _, is_cached_1 = load_yaml(test_file)
        self.assertFalse(is_cached_1)

        # Second load - cache hit
        data, is_cached_2 = load_yaml(test_file)
        self.assertTrue(is_cached_2)
        self.assertEqual(data, {"key": "value"})

    def test_load_yaml_cache_disabled(self):
        """Test load without caching."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        disable_yaml_caching()
        data, is_cached = load_yaml(test_file)

        self.assertFalse(is_cached)
        self.assertEqual(data, {"key": "value"})

        enable_yaml_caching()

    def test_load_yaml_file_not_found(self):
        """Test loading non-existent file raises error."""
        missing_file = Path(self.temp_dir) / "missing.yaml"

        with self.assertRaises(Exception):  # MidicoderError
            load_yaml(missing_file)


class TestLoadYAMLUnsafe(TestCase):
    """Test load_yaml_unsafe function."""

    def setUp(self):
        """Setup before each test."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_valid_yaml_unsafe(self):
        """Test loading valid YAML without validation."""
        test_file = Path(self.temp_dir) / "test.yaml"
        test_file.write_text("key: value")

        data = load_yaml_unsafe(test_file)
        self.assertEqual(data, {"key": "value"})

    def test_load_missing_file_unsafe(self):
        """Test loading missing file returns None."""
        missing_file = Path(self.temp_dir) / "missing.yaml"

        data = load_yaml_unsafe(missing_file)
        self.assertIsNone(data)

    def test_load_invalid_yaml_unsafe(self):
        """Test loading invalid YAML returns None."""
        test_file = Path(self.temp_dir) / "invalid.yaml"
        test_file.write_text("invalid: yaml: content: [")

        data = load_yaml_unsafe(test_file)
        self.assertIsNone(data)


# ============================================================================
# load_projection_tree Tests
# ============================================================================


class TestLoadProjectionTree(TestCase):
    """Test load_projection_tree function."""

    def setUp(self):
        """Setup before each test."""
        self.temp_dir = tempfile.mkdtemp()
        clear_yaml_cache()
        enable_yaml_caching()

    def tearDown(self):
        """Cleanup after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        clear_yaml_cache()
        enable_yaml_caching()

    def test_load_empty_tree(self):
        """Test loading empty DSL directory."""
        # Create empty directory
        tree = load_projection_tree(Path(self.temp_dir))
        self.assertEqual(tree.node_count(), 0)

    def test_load_entities(self):
        """Test loading entities.yaml."""
        entities_file = Path(self.temp_dir) / "entities.yaml"
        entities_file.write_text("""
entities:
  - id: Order
    description: Order entity
    fields:
      - name: order_id
        type: string
      - name: total
        type: decimal
    primary_key: order_id
    tenant_scope: tenant_isolated
""")

        tree = load_projection_tree(Path(self.temp_dir))
        self.assertEqual(tree.node_count(), 1)
        self.assertEqual(len(tree.get_entities()), 1)

        order = tree.get_node("Order")
        self.assertEqual(order.kind, NodeKind.ENTITY)
        self.assertEqual(order.params["primary_key"], "order_id")

    def test_load_commands(self):
        """Test loading commands.yaml."""
        commands_file = Path(self.temp_dir) / "commands.yaml"
        commands_file.write_text("""
commands:
  - id: CreateOrder
    description: Create a new order
    input:
      - name: product_id
        type: string
      - name: quantity
        type: int
    category: create
    writes_to:
      - Order
""")

        tree = load_projection_tree(Path(self.temp_dir))
        self.assertEqual(tree.node_count(), 1)
        self.assertEqual(len(tree.get_commands()), 1)

        cmd = tree.get_node("CreateOrder")
        self.assertEqual(cmd.kind, NodeKind.COMMAND)
        self.assertEqual(cmd.params["category"], "create")

    def test_load_multiple_files(self):
        """Test loading multiple YAML files."""
        # Entities
        (Path(self.temp_dir) / "entities.yaml").write_text("""
entities:
  - id: Product
    fields:
      - name: id
        type: string
""")

        # Commands
        (Path(self.temp_dir) / "commands.yaml").write_text("""
commands:
  - id: CreateProduct
    input: []
    category: create
""")

        # Queries
        (Path(self.temp_dir) / "queries.yaml").write_text("""
queries:
  - id: GetProduct
    returns: []
""")

        tree = load_projection_tree(Path(self.temp_dir))
        self.assertEqual(tree.node_count(), 3)
        self.assertEqual(tree.kind_count(NodeKind.ENTITY), 1)
        self.assertEqual(tree.kind_count(NodeKind.COMMAND), 1)
        self.assertEqual(tree.kind_count(NodeKind.QUERY), 1)

    def test_load_nonexistent_directory(self):
        """Test loading non-existent directory raises error."""
        nonexistent = Path(self.temp_dir) / "nonexistent"

        with self.assertRaises(Exception):  # MidicoderError
            load_projection_tree(nonexistent)

    def test_duplicate_node_id_raises_error(self):
        """Test duplicate node IDs raise error."""
        entities_file = Path(self.temp_dir) / "entities.yaml"
        entities_file.write_text("""
entities:
  - id: Duplicate
    fields: []
""")

        # Create another file with same ID
        values_file = Path(self.temp_dir) / "value-objects.yaml"
        values_file.write_text("""
value_objects:
  - id: Duplicate
    fields: []
""")

        with self.assertRaises(Exception):  # MidicoderError
            load_projection_tree(Path(self.temp_dir))


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])