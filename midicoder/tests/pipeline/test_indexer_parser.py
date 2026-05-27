"""
Tests cho parser module.

Test cases:
- detect_language()
- is_binary_file()
- compute_content_hash()
- parse_python_file()
- parse_typescript_file()
- parse_file()
- parse_directory()
"""

import os
import tempfile
import pytest

from midicoder.pipeline.indexer.parser import (
    SymbolType,
    Symbol,
    Relationship,
    ParsedFile,
    detect_language,
    is_binary_file,
    compute_content_hash,
    parse_python_file,
    parse_typescript_file,
    parse_file,
    parse_directory,
)


class TestDetectLanguage:
    """Tests cho detect_language()."""
    
    def test_python_file(self):
        """Test detect Python file."""
        assert detect_language("test.py") == "python"
        assert detect_language("path/to/file.py") == "python"
    
    def test_typescript_file(self):
        """Test detect TypeScript file."""
        assert detect_language("test.ts") == "typescript"
        assert detect_language("test.tsx") == "typescript"
    
    def test_javascript_file(self):
        """Test detect JavaScript file."""
        assert detect_language("test.js") == "javascript"
        assert detect_language("test.jsx") == "javascript"
    
    def test_other_languages(self):
        """Test detect other languages."""
        assert detect_language("test.go") == "go"
        assert detect_language("test.rs") == "rust"
        assert detect_language("test.java") == "java"
        assert detect_language("test.cs") == "csharp"
    
    def test_unknown_extension(self):
        """Test unknown file extension."""
        assert detect_language("test.xyz") == "unknown"
        assert detect_language("README") == "unknown"


class TestIsBinaryFile:
    """Tests cho is_binary_file()."""
    
    def test_text_file(self):
        """Test text file detection."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, World!")
            f.flush()
            f.close()  # Close file before checking
            assert is_binary_file(f.name) is False
            os.unlink(f.name)
    
    def test_binary_file(self):
        """Test binary file detection."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            f.close()  # Close file before checking
            assert is_binary_file(f.name) is True
            os.unlink(f.name)
    
    def test_nonexistent_file(self):
        """Test nonexistent file."""
        assert is_binary_file("/nonexistent/file.bin") is True


class TestComputeContentHash:
    """Tests cho compute_content_hash()."""
    
    def test_empty_string(self):
        """Test empty string hash."""
        hash_val = compute_content_hash("")
        assert len(hash_val) == 64  # SHA-256 hex string
    
    def test_known_content(self):
        """Test known content hash."""
        hash_val = compute_content_hash("Hello, World!")
        # SHA-256 hash of "Hello, World!"
        assert hash_val == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    
    def test_same_content_same_hash(self):
        """Test same content produces same hash."""
        content = "Test content"
        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)
        assert hash1 == hash2
    
    def test_different_content_different_hash(self):
        """Test different content produces different hash."""
        hash1 = compute_content_hash("Content A")
        hash2 = compute_content_hash("Content B")
        assert hash1 != hash2


class TestParsePythonFile:
    """Tests cho parse_python_file()."""
    
    def test_parse_simple_function(self):
        """Test parse simple Python function."""
        content = """
def greet(name):
    \"\"\"Greet someone.\"\"\"
    return f"Hello, {name}!"
"""
        symbols, relationships = parse_python_file("test.py", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "greet"
        assert symbols[0].symbol_type == SymbolType.FUNCTION
        assert symbols[0].description == "Greet someone."
    
    def test_parse_function_with_type_hints(self):
        """Test parse function with type hints."""
        content = """
def add(a: int, b: int) -> int:
    return a + b
"""
        symbols, _ = parse_python_file("test.py", content)
        
        assert len(symbols) == 1
        assert symbols[0].signature == "def add(a: int, b: int) -> int"
    
    def test_parse_class(self):
        """Test parse Python class."""
        content = """
class Person:
    def __init__(self, name):
        self.name = name
"""
        symbols, _ = parse_python_file("test.py", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "Person"
        assert symbols[0].symbol_type == SymbolType.CLASS
    
    def test_parse_class_inheritance(self):
        """Test parse class with inheritance."""
        content = """
class Animal:
    pass

class Dog(Animal):
    pass
"""
        symbols, relationships = parse_python_file("test.py", content)
        
        assert len(symbols) == 2
        # Check inheritance relationship
        extends_rels = [r for r in relationships if r.relationship_type == "extends"]
        assert len(extends_rels) == 1
        assert extends_rels[0].source_name == "Dog"
        assert extends_rels[0].target_name == "Animal"
    
    def test_parse_imports(self):
        """Test parse imports."""
        content = """
import os
from pathlib import Path
"""
        _, relationships = parse_python_file("test.py", content)
        
        import_rels = [r for r in relationships if r.relationship_type == "imports"]
        assert len(import_rels) >= 2


class TestParseTypescriptFile:
    """Tests cho parse_typescript_file()."""
    
    def test_parse_function(self):
        """Test parse TypeScript function."""
        content = """
function greet(name: string): string {
    return `Hello, ${name}!`;
}
"""
        symbols, _ = parse_typescript_file("test.ts", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "greet"
        assert symbols[0].symbol_type == SymbolType.FUNCTION
    
    def test_parse_arrow_function(self):
        """Test parse arrow function."""
        # Test with return type annotation
        content = """
const add = (a, b) => a + b;
"""
        symbols, _ = parse_typescript_file("test.ts", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "add"
    
    def test_parse_class(self):
        """Test parse TypeScript class."""
        content = """
class Person {
    name: string;
    constructor(name: string) {
        this.name = name;
    }
}
"""
        symbols, _ = parse_typescript_file("test.ts", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "Person"
        assert symbols[0].symbol_type == SymbolType.CLASS
    
    def test_parse_interface(self):
        """Test parse TypeScript interface."""
        content = """
interface User {
    id: number;
    name: string;
}
"""
        symbols, _ = parse_typescript_file("test.ts", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "User"
        assert symbols[0].symbol_type == SymbolType.INTERFACE
    
    def test_parse_type_alias(self):
        """Test parse TypeScript type alias."""
        content = """
type UserId = number;
"""
        symbols, _ = parse_typescript_file("test.ts", content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "UserId"
        assert symbols[0].symbol_type == SymbolType.TYPE


class TestParseFile:
    """Tests cho parse_file()."""
    
    def test_parse_python_file(self):
        """Test parse actual Python file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def hello():
    return "Hello, World!"
""")
            f.flush()
            f.close()  # Close before parsing
            
            result = parse_file(f.name)
            os.unlink(f.name)
        
        assert result is not None
        assert result.language == "python"
        assert len(result.symbols) == 1
        assert result.symbols[0].name == "hello"
    
    def test_parse_nonexistent_file(self):
        """Test parse nonexistent file."""
        result = parse_file("/nonexistent/file.py")
        assert result is None
    
    def test_parse_binary_file(self):
        """Test parse binary file."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            f.close()  # Close before parsing
            
            result = parse_file(f.name)
            os.unlink(f.name)
        
        assert result is None


class TestParseDirectory:
    """Tests cho parse_directory()."""
    
    def test_parse_directory(self):
        """Test parse directory with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            with open(os.path.join(tmpdir, "test1.py"), "w") as f:
                f.write("def func1(): pass")
            
            with open(os.path.join(tmpdir, "test2.py"), "w") as f:
                f.write("def func2(): pass")
            
            results = parse_directory(tmpdir)
        
        assert len(results) == 2
    
    def test_exclude_directories(self):
        """Test exclude directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create included file
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("def func(): pass")
            
            # Create excluded directory
            excluded_dir = os.path.join(tmpdir, "node_modules")
            os.makedirs(excluded_dir)
            with open(os.path.join(excluded_dir, "excluded.py"), "w") as f:
                f.write("def excluded(): pass")
            
            results = parse_directory(tmpdir)
        
        # Should only include test.py, not excluded.py
        assert len(results) == 1
        assert results[0].file_path.endswith("test.py")


class TestSymbol:
    """Tests cho Symbol class."""
    
    def test_symbol_creation(self):
        """Test create Symbol."""
        symbol = Symbol(
            name="test_function",
            symbol_type=SymbolType.FUNCTION,
            file_path="/path/to/file.py",
            line_start=1,
            line_end=10,
        )
        
        assert symbol.name == "test_function"
        assert symbol.symbol_type == SymbolType.FUNCTION
    
    def test_symbol_to_dict(self):
        """Test Symbol.to_dict()."""
        symbol = Symbol(
            name="test",
            symbol_type=SymbolType.CLASS,
            file_path="test.py",
            line_start=1,
            line_end=5,
            signature="class Test",
            description="A test class",
        )
        
        data = symbol.to_dict()
        assert data["name"] == "test"
        assert data["type"] == "class"
        assert data["file_path"] == "test.py"


class TestRelationship:
    """Tests cho Relationship class."""
    
    def test_relationship_creation(self):
        """Test create Relationship."""
        rel = Relationship(
            source_name="Child",
            target_name="Parent",
            relationship_type="extends",
            file_path="test.py",
        )
        
        assert rel.source_name == "Child"
        assert rel.target_name == "Parent"
        assert rel.relationship_type == "extends"
    
    def test_relationship_to_dict(self):
        """Test Relationship.to_dict()."""
        rel = Relationship(
            source_name="A",
            target_name="B",
            relationship_type="calls",
            file_path="test.py",
        )
        
        data = rel.to_dict()
        assert data["source_name"] == "A"
        assert data["target_name"] == "B"
        assert data["relationship_type"] == "calls"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])