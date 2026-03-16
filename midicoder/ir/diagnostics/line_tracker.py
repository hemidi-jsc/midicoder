"""Line number tracking for YAML files using ruamel.yaml.

This module provides utilities to extract line numbers from YAML data
loaded with ruamel.yaml, enabling precise error reporting.
"""

from __future__ import annotations

from typing import Any


def _list_item_line(obj: Any, index: int) -> int | None:
    """Get line number for an item in a ruamel.yaml sequence."""
    if not hasattr(obj, "lc") or not hasattr(obj.lc, "data"):
        return None
    try:
        data = obj.lc.data
        entry = None
        if isinstance(data, dict):
            entry = data.get(index)
        elif isinstance(data, list):
            if index < 0 or index >= len(data):
                return None
            entry = data[index]
        else:
            return None
        if entry is None:
            return None
        # ruamel stores (line, col) tuples or line ints depending on version
        if isinstance(entry, (list, tuple)) and entry:
            return entry[0] + 1
        if isinstance(entry, int):
            return entry + 1
    except (AttributeError, IndexError, TypeError):
        return None
    return None


def get_line_number(obj: Any, key: str | int | None = None) -> int | None:
    """
    Extract line number from a ruamel.yaml object.
    
    Args:
        obj: The YAML object (dict, list, or primitive)
        key: Optional key/index to get line number for a specific item
    
    Returns:
        Line number (1-indexed) or None if not available
    
    Examples:
        >>> data = yaml.load(yaml_string)  # ruamel.yaml
        >>> get_line_number(data)  # Line of root object
        1
        >>> get_line_number(data, 'entities')  # Line of 'entities' key
        5
        >>> get_line_number(data['entities'], 0)  # Line of first entity
        6
    """
    try:
        # ruamel.yaml stores line info in .lc attribute
        if hasattr(obj, 'lc'):
            if key is not None:
                # List item
                if isinstance(obj, list) and isinstance(key, int):
                    line = _list_item_line(obj, key)
                    if line:
                        return line
                # Dict key
                line_col = obj.lc.key(key) if hasattr(obj.lc, 'key') else None
                if line_col:
                    return line_col[0] + 1  # Convert to 1-indexed
            else:
                # Get line number of the object itself
                if hasattr(obj.lc, 'line'):
                    return obj.lc.line + 1  # Convert to 1-indexed
        
        # Fallback: check if object has __line__ attribute (custom tracking)
        if hasattr(obj, '__line__'):
            return obj.__line__
        
    except (AttributeError, KeyError, TypeError):
        pass
    
    return None


def get_line_range(obj: Any, key: str | int | None = None) -> tuple[int | None, int | None]:
    """
    Extract line range (start, end) from a ruamel.yaml object.
    
    Args:
        obj: The YAML object (dict, list, or primitive)
        key: Optional key/index to get line range for a specific item
    
    Returns:
        Tuple of (line_start, line_end) both 1-indexed, or (None, None) if not available
    
    Examples:
        >>> data = yaml.load(yaml_string)  # ruamel.yaml
        >>> get_line_range(data['entities'][0])
        (10, 25)
    """
    line_start = None
    line_end = None
    
    try:
        # If key is specified, get the value first
        target_obj = obj
        if key is not None:
            if isinstance(obj, dict):
                target_obj = obj.get(key)
            elif isinstance(obj, list) and isinstance(key, int):
                target_obj = obj[key] if 0 <= key < len(obj) else None
            
            if target_obj is None:
                return (None, None)
        
        # Try to get line_start from the object
        if key is not None:
            if isinstance(obj, list) and isinstance(key, int):
                line_start = _list_item_line(obj, key)
                if line_start is None and hasattr(obj, 'lc'):
                    line_col = obj.lc.key(key) if hasattr(obj.lc, 'key') else None
                    if line_col:
                        line_start = line_col[0] + 1
            elif hasattr(obj, 'lc'):
                # Get start line from key position
                line_col = obj.lc.key(key) if hasattr(obj.lc, 'key') else None
                if line_col:
                    line_start = line_col[0] + 1
        elif hasattr(target_obj, 'lc') and hasattr(target_obj.lc, 'line'):
            line_start = target_obj.lc.line + 1
        
        # Try to get line_end
        if hasattr(target_obj, 'lc'):
            # For dict/list objects, try to find the last line
            if isinstance(target_obj, dict) and hasattr(target_obj.lc, 'data'):
                # Get all line numbers from keys and values
                all_lines = []
                for k in target_obj.keys():
                    key_line = target_obj.lc.key(k) if hasattr(target_obj.lc, 'key') else None
                    if key_line:
                        all_lines.append(key_line[0])
                    value_line = target_obj.lc.value(k) if hasattr(target_obj.lc, 'value') else None
                    if value_line:
                        all_lines.append(value_line[0])
                
                if all_lines:
                    line_end = max(all_lines) + 1
            
            elif isinstance(target_obj, list) and hasattr(target_obj.lc, 'data'):
                # Get last item's line
                if len(target_obj) > 0:
                    last_item_line = get_line_number(target_obj, len(target_obj) - 1)
                    if last_item_line:
                        line_end = last_item_line
        
        # Fallback: if we have start but not end, estimate based on content
        if line_start is not None and line_end is None:
            if isinstance(target_obj, dict):
                # Estimate ~1 line per field + 2 for wrapper
                line_end = line_start + len(target_obj) + 1
            elif isinstance(target_obj, list):
                # Estimate based on list length
                line_end = line_start + len(target_obj)
            else:
                # Single line object
                line_end = line_start
        
        # Custom tracking fallback
        if hasattr(target_obj, '__line_start__') and hasattr(target_obj, '__line_end__'):
            line_start = target_obj.__line_start__
            line_end = target_obj.__line_end__
        
    except (AttributeError, KeyError, TypeError, IndexError):
        pass
    
    return (line_start, line_end)


def get_item_line_number(parent: Any, index: int) -> int | None:
    """
    Get line number for an item in a list.
    
    Args:
        parent: Parent list/array
        index: Index of item in list
    
    Returns:
        Line number or None
    """
    return get_line_number(parent, index)


def get_key_line_number(parent: Any, key: str) -> int | None:
    """
    Get line number for a key in a dict.
    
    Args:
        parent: Parent dict
        key: Key name
    
    Returns:
        Line number or None
    """
    return get_line_number(parent, key)


def attach_line_numbers(data: Any, parent_line: int | None = None) -> None:
    """
    Recursively attach line numbers to nested structures.
    
    This is useful when passing data to Pydantic models that don't
    preserve ruamel.yaml's line tracking.
    
    Args:
        data: YAML data structure
        parent_line: Line number of parent (for fallback)
    """
    if data is None:
        return
    
    current_line = get_line_number(data) or parent_line
    
    if isinstance(data, dict):
        for key, value in data.items():
            key_line = get_key_line_number(data, key) or current_line
            
            # Attach line to nested structure
            if isinstance(value, (dict, list)):
                attach_line_numbers(value, key_line)
            elif hasattr(value, '__dict__'):
                # For objects, try to attach
                try:
                    value.__line__ = key_line
                except (AttributeError, TypeError):
                    pass
    
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            item_line = get_item_line_number(data, idx) or current_line
            
            if isinstance(item, (dict, list)):
                attach_line_numbers(item, item_line)
            elif hasattr(item, '__dict__'):
                try:
                    item.__line__ = item_line
                except (AttributeError, TypeError):
                    pass


def format_line_context(file_path: str, line_number: int, context_lines: int = 2) -> str:
    """
    Format code context around a specific line for error messages.
    
    Args:
        file_path: Path to source file
        line_number: Line number to highlight (1-indexed)
        context_lines: Number of lines before/after to show
    
    Returns:
        Formatted string with line context and arrow indicator
    
    Example:
        13 |   input:
        14 |     - name: user_id
        15 |       type: Entity:usr     # ← Error here
        16 |       required: true
        17 |
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Calculate range
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        # Format output
        result = []
        for i in range(start, end):
            line_num = i + 1
            line_content = lines[i].rstrip()
            
            # Add arrow indicator for error line
            if line_num == line_number:
                result.append(f"  {line_num:3d} | {line_content}     # ← Error here")
            else:
                result.append(f"  {line_num:3d} | {line_content}")
        
        return "\n".join(result)
    
    except (FileNotFoundError, IOError, IndexError):
        return ""


def get_nested_line_number(data: Any, path: str) -> int | None:
    """
    Get line number for a nested path like "entities[0].fields[1].name".
    
    Args:
        data: Root YAML data
        path: Dot-separated path with array indices
    
    Returns:
        Line number or None
    
    Example:
        >>> get_nested_line_number(data, "entities[0].fields[1]")
        42
    """
    current = data
    parent = None
    last_key = None
    
    # Parse path: "entities[0].fields[1].name"
    parts = path.replace('[', '.').replace(']', '').split('.')
    
    try:
        for part in parts:
            if not part:
                continue
            
            parent = current
            
            # Check if it's an array index
            if part.isdigit():
                index = int(part)
                last_key = index
                current = current[index]
            else:
                last_key = part
                current = current[part]
        
        # Try to get line number from final object
        if parent is not None and last_key is not None:
            line = get_line_number(parent, last_key)
            if line:
                return line
        
        # Fallback: line of current object
        return get_line_number(current)
    
    except (KeyError, IndexError, TypeError):
        return None


def extract_line_info(obj: Any, key: str | int | None = None) -> dict[str, int | None]:
    """
    Extract comprehensive line information from a ruamel.yaml object.
    
    Args:
        obj: The YAML object (dict, list, or primitive)
        key: Optional key/index to get info for a specific item
    
    Returns:
        Dictionary with 'start', 'end', and 'single' line numbers
    
    Example:
        >>> info = extract_line_info(data['entities'], 0)
        >>> # {'start': 10, 'end': 25, 'single': 10}
    """
    line_start, line_end = get_line_range(obj, key)
    line_single = get_line_number(obj, key)
    
    return {
        'start': line_start,
        'end': line_end,
        'single': line_single or line_start,  # Fallback to start if single not available
    }


__all__ = [
    "get_line_number",
    "get_line_range",
    "get_item_line_number", 
    "get_key_line_number",
    "attach_line_numbers",
    "format_line_context",
    "get_nested_line_number",
    "extract_line_info",
]
