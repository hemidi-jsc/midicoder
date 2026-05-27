"""
Mô-đun parse source code để extract symbols và relationships.

Hỗ trợ nhiều ngôn ngữ:
- Python: functions, classes, variables
- TypeScript/JavaScript: functions, classes, interfaces
- Và các ngôn ngữ khác

Sử dụng:
    from midicoder.pipeline.indexer.parser import parse_file, Symbol, SymbolType
    
    # Parse một file
    symbols = parse_file("/path/to/file.py")
    for symbol in symbols:
        print(symbol.name, symbol.type)
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SymbolType(str, Enum):
    """
    Các loại symbols có thể extract từ source code.
    
    Mapping:
    - FUNCTION: function, method, procedure
    - CLASS: class, struct
    - INTERFACE: interface, protocol, abstract class
    - VARIABLE: global variable, constant
    - ENUM: enum definition
    - TYPE: type alias, type definition
    - MODULE: module, package
    - COMPONENT: React/Angular component
    """
    FUNCTION = "function"
    CLASS = "class"
    INTERFACE = "interface"
    VARIABLE = "variable"
    ENUM = "enum"
    TYPE = "type"
    MODULE = "module"
    COMPONENT = "component"


@dataclass
class Symbol:
    """
    Đại diện cho một symbol trong source code.
    
    Attributes:
        name: Tên của symbol
        symbol_type: Loại symbol (SymbolType enum)
        file_path: Đường dẫn file chứa symbol
        line_start: Dòng bắt đầu
        line_end: Dòng kết thúc
        signature: Signature của symbol (ví dụ: "def foo(bar: int) -> str")
        description: Mô tả (từ docstring hoặc comment)
        language: Ngôn ngữ của file
        content_snippet: Đoạn code ngắn xung quanh symbol (cho context)
        references: Danh sách symbols mà symbol này references
    """
    name: str
    symbol_type: SymbolType
    file_path: str
    line_start: int
    line_end: int
    signature: str = ""
    description: str = ""
    language: str = ""
    content_snippet: str = ""
    references: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """
        Chuyển symbol thành dictionary.
        
        Returns:
            Dictionary representation của symbol
        """
        return {
            "name": self.name,
            "type": self.symbol_type.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "signature": self.signature,
            "description": self.description,
            "language": self.language,
            "content_snippet": self.content_snippet,
            "references": self.references,
        }


@dataclass
class Relationship:
    """
    Đại diện cho relationship giữa hai symbols.
    
    Ví dụ:
    - Function A calls Function B
    - Class C extends Class D
    - Module E imports Module F
    
    Attributes:
        source_name: Tên symbol nguồn
        target_name: Tên symbol đích
        relationship_type: Loại relationship
        file_path: File chứa relationship này
    """
    source_name: str
    target_name: str
    relationship_type: str  # calls, imports, extends, implements
    file_path: str
    
    def to_dict(self) -> dict[str, Any]:
        """Chuyển relationship thành dictionary."""
        return {
            "source_name": self.source_name,
            "target_name": self.target_name,
            "relationship_type": self.relationship_type,
            "file_path": self.file_path,
        }


@dataclass
class ParsedFile:
    """
    Kết quả parse một file source code.
    
    Attributes:
        file_path: Đường dẫn file
        content: Nội dung file
        content_hash: SHA-256 hash của content
        language: Ngôn ngữ detected
        size_bytes: Kích thước file
        symbols: Danh sách symbols extract được
        relationships: Danh sách relationships
    """
    file_path: str
    content: str
    content_hash: str
    language: str
    size_bytes: int
    symbols: list[Symbol] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)


def detect_language(file_path: str) -> str:
    """
    Detect ngôn ngữ của file dựa trên extension.
    
    Args:
        file_path: Đường dẫn file
        
    Returns:
        Tên ngôn ngữ (python, typescript, javascript, etc.)
    """
    extension_map = {
        ".py": "python",
        ".ts": "typescript",
        ".js": "javascript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c_header",
        ".hpp": "cpp_header",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
    }
    
    ext = Path(file_path).suffix.lower()
    return extension_map.get(ext, "unknown")


def is_binary_file(file_path: str) -> bool:
    """
    Kiểm tra xem file có phải binary không.
    
    Args:
        file_path: Đường dẫn file
        
    Returns:
        True nếu là binary file
    """
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            # Kiểm tra null bytes - dấu hiệu của binary file
            if b"\x00" in chunk:
                return True
        return False
    except (IOError, OSError):
        return True


def compute_content_hash(content: str) -> str:
    """
    Tính SHA-256 hash của content.
    
    Args:
        content: Nội dung file
        
    Returns:
        SHA-256 hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_python_file(file_path: str, content: str) -> tuple[list[Symbol], list[Relationship]]:
    """
    Parse Python file để extract symbols và relationships.
    
    Args:
        file_path: Đường dẫn file Python
        content: Nội dung file
        
    Returns:
        Tuple của (symbols list, relationships list)
    """
    symbols = []
    relationships = []
    lines = content.split("\n")
    
    # Simple regex-based parsing (production sẽ dùng AST)
    import re
    
    # Parse functions
    func_pattern = re.compile(r"^def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([\w\[\]\s,]+))?\s*:")
    class_pattern = re.compile(r"^class\s+(\w+)(?:\s*\(([^)]*)\))?\s*:")
    import_pattern = re.compile(r"^(?:from\s+(\w+)\s+)?import\s+([\w,]+)")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect function definition
        func_match = func_pattern.match(line)
        if func_match:
            func_name = func_match.group(1)
            params = func_match.group(2) or ""
            return_type = func_match.group(3) or ""
            
            # Tìm line_end (đến function tiếp theo hoặc class hoặc cuối file)
            end_line = i + 1
            while end_line < len(lines):
                next_line = lines[end_line].strip()
                if next_line and not next_line.startswith("#") and not next_line.startswith('"""') and not next_line.startswith("'''"):
                    if next_line.startswith("def ") or next_line.startswith("class "):
                        break
                # Check indentation - nếu về 0 thì hết function
                if lines[end_line] and not lines[end_line][0].isspace() and lines[end_line][0] not in "#\"'":
                    break
                end_line += 1
            
            # Extract docstring
            docstring = ""
            if i + 1 < len(lines) and ('"""' in lines[i + 1] or "'''" in lines[i + 1]):
                docstring = lines[i + 1].strip().strip('"""').strip("'''")
            
            signature = f"def {func_name}({params})"
            if return_type:
                signature += f" -> {return_type}"
            
            # Get content snippet (5 lines around)
            start_snippet = max(0, i - 2)
            end_snippet = min(len(lines), end_line + 2)
            snippet = "\n".join(lines[start_snippet:end_snippet])
            
            symbols.append(Symbol(
                name=func_name,
                symbol_type=SymbolType.FUNCTION,
                file_path=file_path,
                line_start=i + 1,
                line_end=end_line,
                signature=signature,
                description=docstring,
                language="python",
                content_snippet=snippet,
            ))
            
            i = end_line
            continue
        
        # Detect class definition
        class_match = class_pattern.match(line)
        if class_match:
            class_name = class_match.group(1)
            parent_classes = class_match.group(2)
            
            # Find class end
            end_line = i + 1
            indent_level = None
            while end_line < len(lines):
                if lines[end_line].strip():
                    current_indent = len(lines[end_line]) - len(lines[end_line].lstrip())
                    if indent_level is None:
                        indent_level = current_indent
                    elif current_indent <= (indent_level or 0) and not lines[end_line].strip().startswith("#"):
                        break
                end_line += 1
            
            # Get snippet
            start_snippet = max(0, i - 1)
            end_snippet = min(len(lines), end_line + 1)
            snippet = "\n".join(lines[start_snippet:end_snippet])
            
            signature = f"class {class_name}"
            if parent_classes:
                signature += f"({parent_classes})"
            
            symbols.append(Symbol(
                name=class_name,
                symbol_type=SymbolType.CLASS,
                file_path=file_path,
                line_start=i + 1,
                line_end=end_line,
                signature=signature,
                language="python",
                content_snippet=snippet,
            ))
            
            # Track inheritance relationship
            if parent_classes:
                for parent in parent_classes.split(","):
                    parent_name = parent.strip().split("[")[0]  # Handle Generic[T]
                    if parent_name and parent_name not in ("object",):
                        relationships.append(Relationship(
                            source_name=class_name,
                            target_name=parent_name,
                            relationship_type="extends",
                            file_path=file_path,
                        ))
            
            i = end_line
            continue
        
        # Detect imports
        import_match = import_pattern.match(line)
        if import_match:
            module = import_match.group(1) or ""
            imports = import_match.group(2)
            
            for imp in imports.split(","):
                imp_name = imp.strip().split(" as ")[0]  # Handle "import X as Y"
                if module:
                    relationships.append(Relationship(
                        source_name="__module__",
                        target_name=f"{module}.{imp_name}",
                        relationship_type="imports",
                        file_path=file_path,
                    ))
                else:
                    relationships.append(Relationship(
                        source_name="__module__",
                        target_name=imp_name,
                        relationship_type="imports",
                        file_path=file_path,
                    ))
        
        i += 1
    
    return symbols, relationships


def parse_typescript_file(file_path: str, content: str) -> tuple[list[Symbol], list[Relationship]]:
    """
    Parse TypeScript/JavaScript file để extract symbols.
    
    Args:
        file_path: Đường dẫn file TS/JS
        content: Nội dung file
        
    Returns:
        Tuple của (symbols list, relationships list)
    """
    symbols = []
    relationships = []
    lines = content.split("\n")
    
    import re
    
    # Patterns for TypeScript/JavaScript
    func_pattern = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(")
    arrow_pattern = re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(?([^)]*)\)?\s*=>")
    class_pattern = re.compile(r"^(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?.*\{")
    interface_pattern = re.compile(r"^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+(\w+))?")
    type_pattern = re.compile(r"^(?:export\s+)?type\s+(\w+)\s*=")
    import_pattern = re.compile(r"^import\s+.*\s+from\s+['\"]([^'\"]+)['\"]")
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Function
        func_match = func_pattern.match(stripped)
        if func_match:
            func_name = func_match.group(1)
            symbols.append(Symbol(
                name=func_name,
                symbol_type=SymbolType.FUNCTION,
                file_path=file_path,
                line_start=i + 1,
                line_end=i + 1,
                signature=f"function {func_name}(...)",
                language="typescript",
                content_snippet=stripped,
            ))
        
        # Arrow function
        arrow_match = arrow_pattern.match(stripped)
        if arrow_match:
            func_name = arrow_match.group(1)
            symbols.append(Symbol(
                name=func_name,
                symbol_type=SymbolType.FUNCTION,
                file_path=file_path,
                line_start=i + 1,
                line_end=i + 1,
                signature=f"const {func_name} = (...) => ...",
                language="typescript",
                content_snippet=stripped,
            ))
        
        # Class
        class_match = class_pattern.match(stripped)
        if class_match:
            class_name = class_match.group(1)
            extends = class_match.group(2)
            implements = class_match.group(3)
            
            signature = f"class {class_name}"
            if extends:
                signature += f" extends {extends}"
                relationships.append(Relationship(
                    source_name=class_name,
                    target_name=extends,
                    relationship_type="extends",
                    file_path=file_path,
                ))
            if implements:
                signature += f" implements {implements}"
            
            symbols.append(Symbol(
                name=class_name,
                symbol_type=SymbolType.CLASS,
                file_path=file_path,
                line_start=i + 1,
                line_end=i + 1,
                signature=signature,
                language="typescript",
                content_snippet=stripped,
            ))
        
        # Interface
        interface_match = interface_pattern.match(stripped)
        if interface_match:
            interface_name = interface_match.group(1)
            extends = interface_match.group(2)
            
            symbols.append(Symbol(
                name=interface_name,
                symbol_type=SymbolType.INTERFACE,
                file_path=file_path,
                line_start=i + 1,
                line_end=i + 1,
                signature=f"interface {interface_name}",
                language="typescript",
                content_snippet=stripped,
            ))
            
            if extends:
                relationships.append(Relationship(
                    source_name=interface_name,
                    target_name=extends,
                    relationship_type="extends",
                    file_path=file_path,
                ))
        
        # Type alias
        type_match = type_pattern.match(stripped)
        if type_match:
            type_name = type_match.group(1)
            symbols.append(Symbol(
                name=type_name,
                symbol_type=SymbolType.TYPE,
                file_path=file_path,
                line_start=i + 1,
                line_end=i + 1,
                signature=f"type {type_name} = ...",
                language="typescript",
                content_snippet=stripped,
            ))
        
        # Import
        import_match = import_pattern.match(stripped)
        if import_match:
            module = import_match.group(1)
            relationships.append(Relationship(
                source_name="__module__",
                target_name=module,
                relationship_type="imports",
                file_path=file_path,
            ))
    
    return symbols, relationships


def parse_file(file_path: str) -> ParsedFile | None:
    """
    Parse một file source code để extract symbols và relationships.
    
    Args:
        file_path: Đường dẫn file cần parse
        
    Returns:
        ParsedFile object hoặc None nếu file không thể parse
        
    Raises:
        FileNotFoundError: Nếu file không tồn tại
        UnicodeDecodeError: Nếu file không thể decode thành UTF-8
    """
    # Read file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return None
    except UnicodeDecodeError:
        # Try latin-1 as fallback
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception:
            return None
    
    # Check if binary
    if is_binary_file(file_path):
        return None
    
    # Detect language
    language = detect_language(file_path)
    
    if language == "unknown":
        return None
    
    # Compute hash and size
    content_hash = compute_content_hash(content)
    size_bytes = os.path.getsize(file_path)
    
    # Parse based on language
    symbols = []
    relationships = []
    
    if language == "python":
        symbols, relationships = parse_python_file(file_path, content)
    elif language in ("typescript", "javascript"):
        symbols, relationships = parse_typescript_file(file_path, content)
    # else: Future languages
    
    return ParsedFile(
        file_path=file_path,
        content=content,
        content_hash=content_hash,
        language=language,
        size_bytes=size_bytes,
        symbols=symbols,
        relationships=relationships,
    )


def parse_directory(dir_path: str, exclude_dirs: list[str] = None) -> list[ParsedFile]:
    """
    Parse tất cả files trong một directory.
    
    Args:
        dir_path: Đường dẫn directory
        exclude_dirs: Danh sách thư mục cần exclude
        
    Returns:
        List của ParsedFile objects
    """
    exclude_dirs = exclude_dirs or []
    exclude_dirs.extend([".git", "node_modules", "venv", "__pycache__", "dist", "build", ".midicoder"])
    
    parsed_files = []
    
    for root, dirs, files in os.walk(dir_path):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Check if binary first
            if is_binary_file(file_path):
                continue
            
            # Parse file
            parsed = parse_file(file_path)
            if parsed:
                parsed_files.append(parsed)
    
    return parsed_files


__all__ = [
    "SymbolType",
    "Symbol",
    "Relationship",
    "ParsedFile",
    "detect_language",
    "is_binary_file",
    "compute_content_hash",
    "parse_file",
    "parse_directory",
]