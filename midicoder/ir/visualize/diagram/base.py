"""Base diagram generator for IR visualization."""

from __future__ import annotations

import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


class DiagramGenerator(ABC):
    """Base class for diagram generators."""
    
    def __init__(self, output_dir: Path):
        """Initialize diagram generator.
        
        Args:
            output_dir: Directory to write diagram files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate(self, ir_data: Any) -> list[DiagramOutput]:
        """Generate diagrams from IR data.
        
        Args:
            ir_data: IR data to visualize
            
        Returns:
            List of generated diagram outputs
        """
        pass
    
    def _sanitize_id(self, id_str: str) -> str:
        """Sanitize ID for use in diagram node names.
        
        Args:
            id_str: Original ID string
            
        Returns:
            Sanitized ID safe for Graphviz/Mermaid
        """
        return id_str.replace(":", "_").replace("-", "_").replace(".", "_")
    
    def _escape_label(self, label: str) -> str:
        """Escape label text for diagram output.
        
        Args:
            label: Original label text
            
        Returns:
            Escaped label
        """
        return label.replace('"', '\\"').replace('\n', '\\n')


class DiagramOutput:
    """Output from diagram generation."""
    
    def __init__(
        self,
        diagram_id: str,
        diagram_type: str,
        format: str,
        path: Path,
        sources: list[str] | list[dict[str, Any]],
        template: str | None = None,
        engine: str = "mermaid",
        assets: list[str] | None = None,
    ):
        """Initialize diagram output.
        
        Args:
            diagram_id: Unique identifier for diagram
            diagram_type: Type of diagram (workflow, entity, api, command)
            format: Output format (mmd)
            path: Path to output file
            sources: Source IR elements used to create diagram.
                    Can be list of IDs (legacy) or list of dicts with full metadata:
                    [{"id": "user", "type": "Entity", "file": "entities.yaml", 
                      "line_start": 10, "line_end": 25}]
        """
        self.diagram_id = diagram_id
        self.diagram_type = diagram_type
        self.format = format
        self.path = path
        self.sources = sources
        self.template = template
        self.engine = engine
        self.assets = assets or [str(path.with_suffix(".mmd"))]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for manifest."""
        return {
            "id": self.diagram_id,
            "type": self.diagram_type,
            "format": self.format,
            "path": str(self.path),
            "sources": self.sources,
            "template": self.template,
            "engine": self.engine,
            "assets": self.assets,
        }


def create_source_metadata(
    id: str,
    type: str,
    source: Any = None,
) -> dict[str, Any]:
    """Create source metadata dict for diagram traceability.
    
    Args:
        id: Source element ID
        type: Source element type (Entity, Command, etc.)
        source: SourceMetadata object from IR (optional)
    
    Returns:
        Dictionary with full source metadata
    """
    metadata = {
        "id": id,
        "type": type,
    }
    
    if source is not None and hasattr(source, 'file'):
        metadata["file"] = source.file
        
        if hasattr(source, 'line_start') and source.line_start is not None:
            metadata["line_start"] = source.line_start
        
        if hasattr(source, 'line_end') and source.line_end is not None:
            metadata["line_end"] = source.line_end
        
        if hasattr(source, 'source_order') and source.source_order is not None:
            metadata["source_order"] = source.source_order
    
    return metadata


class MermaidRenderer:
    """Renderer for Mermaid format."""
    
    _theme_path: Path | None = None
    _theme_cache: dict[str, Any] | None = None
    _init_block: str | None = None
    _class_block: str | None = None
    _cli_path: str | None = None
    _cli_version: str | None = None
    
    @classmethod
    def configure(cls, theme_path: Path | None = None) -> None:
        """Configure theme path override."""
        if theme_path is not None:
            cls._theme_path = theme_path
    
    @classmethod
    def render_to_file(cls, mermaid_source: str, output_path: Path, format: str = "mmd") -> list[str]:
        """Write Mermaid source to a .mmd file.
        
        Args:
            mermaid_source: Mermaid source
            output_path: Path to output file (will be .mmd)
            format: Output format (mmd) - reserved for compatibility
            
        Returns:
            List of generated asset paths
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        formatted = cls._apply_theme(mermaid_source)
        formatted = cls._lint_source(formatted)
        
        mmd_path = output_path.with_suffix(".mmd")
        with open(mmd_path, "w", encoding="utf-8") as fh:
            fh.write(formatted)
            fh.write("\n")
        
        assets = [str(mmd_path)]
        svg_path = cls._render_svg_if_available(mmd_path)
        if svg_path:
            assets.append(str(svg_path))
        return assets

    @classmethod
    def _lint_source(cls, source: str) -> str:
        """Apply basic formatting."""
        return "\n".join(line.rstrip() for line in source.splitlines()).strip()

    @classmethod
    def _apply_theme(cls, source: str) -> str:
        """Attach theme init and class definitions."""
        cls._ensure_theme_loaded()
        result = source
        if cls._class_block:
            result = f"{result}\n\n{cls._class_block}"
        return result

    @classmethod
    def _render_svg_if_available(cls, mmd_path: Path) -> str | None:
        cli = cls._detect_mermaid_cli()
        if not cli:
            return None
        svg_path = mmd_path.with_suffix(".svg")
        try:
            subprocess.run(
                [cli, "-i", str(mmd_path), "-o", str(svg_path), "--quiet"],
                check=True,
                capture_output=True,
            )
            return str(svg_path)
        except subprocess.CalledProcessError:
            return None

    @classmethod
    def _detect_mermaid_cli(cls) -> str | None:
        if cls._cli_path is not None:
            return cls._cli_path
        cls._cli_path = shutil.which("mmdc")
        if cls._cli_path:
            cls._cli_version = cls._read_cli_version(cls._cli_path)
        return cls._cli_path

    @classmethod
    def _read_cli_version(cls, cli_path: str) -> str | None:
        try:
            result = subprocess.run(
                [cli_path, "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or None
        except Exception:
            return None

    @classmethod
    def renderer_metadata(cls) -> dict[str, Any]:
        cls._ensure_theme_loaded()
        return {
            "engine": "mermaid",
            "theme_path": str(cls._theme_path) if cls._theme_path else None,
            "cli_path": cls._detect_mermaid_cli(),
            "cli_version": cls._cli_version,
        }

    @classmethod
    def _ensure_theme_loaded(cls) -> None:
        if cls._theme_cache is not None:
            return
        theme_path = cls._theme_path or Path(__file__).resolve().parent.parent / "mermaid_theme.yml"
        cls._theme_path = theme_path
        if not theme_path.exists():
            cls._theme_cache = {}
            cls._init_block = None
            cls._class_block = None
            return
        yaml = YAML(typ="safe")
        data = yaml.load(theme_path.read_text(encoding="utf-8")) or {}
        cls._theme_cache = data
        defaults = data.get("defaults") or {}
        if defaults:
            cls._init_block = f"%%{{init: {json.dumps(defaults, ensure_ascii=False)}}}%%"
        classes = data.get("classes") or {}
        class_lines = []
        for class_name, props in classes.items():
            styles = []
            if props.get("stroke"):
                styles.append(f"stroke:{props['stroke']}")
            if props.get("fill"):
                styles.append(f"fill:{props['fill']}")
            if props.get("textColor"):
                styles.append(f"color:{props['textColor']}")
            if props.get("extra"):
                styles.append(props["extra"])
            if styles:
                class_lines.append(f"classDef {class_name} {' '.join(styles)};")
        cls._class_block = "\n".join(class_lines) if class_lines else None
    
    @staticmethod
    def sanitize_mermaid_id(id_str: str) -> str:
        """Sanitize ID for use in Mermaid node names.
        
        Mermaid has stricter rules than Graphviz for node IDs.
        Only alphanumeric and underscore are safe.
        
        Args:
            id_str: Original ID string
            
        Returns:
            Sanitized ID safe for Mermaid
        """
        import re
        
        # Replace all non-alphanumeric characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', id_str)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it starts with a letter or underscore
        if sanitized and not (sanitized[0].isalpha() or sanitized[0] == "_"):
            sanitized = "n_" + sanitized
        
        # Ensure not empty
        if not sanitized:
            sanitized = "node_unnamed"
        
        return sanitized
    
    @staticmethod
    def escape_mermaid_text(text: str) -> str:
        """Escape text for Mermaid labels.
        
        For Mermaid, we should avoid HTML entities in most contexts.
        Instead, use simple character replacement or removal.
        
        Args:
            text: Original text
            
        Returns:
            Escaped text safe for Mermaid
        """
        # For Mermaid labels, we need to be careful with special characters
        # Replace problematic characters with safe alternatives
        text = text.replace('"', "'")  # Replace double quotes with single quotes
        text = text.replace('\n', ' ')  # Replace newlines with spaces
        text = text.replace('\r', '')   # Remove carriage returns
        
        # Remove or replace other problematic characters
        text = text.replace('#', 'num')
        text = text.replace('&', 'and')
        text = text.replace('<', '[')
        text = text.replace('>', ']')
        
        return text
