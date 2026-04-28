"""
Value Object Computed Field Evaluator

Evaluator cho computed fields với formula evaluation.
Support dependency resolution và lazy evaluation.

Author: Midicoder Team
Version: 2.0.0
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class FormulaError(Exception):
    """
    Error khi formula evaluation thất bại.

    Attributes:
        field_name: Tên field có lỗi
        formula: Formula có lỗi
        message: Error message
        cause: Original exception (nếu có)
    """

    field_name: str
    formula: str
    message: str
    cause: Optional[Exception] = None


class ComputedFieldEvaluator:
    """
    Evaluator cho computed fields.

    Process:
    1. Parse formula string
    2. Resolve dependencies (depends_on fields)
    3. Evaluate formula với provided values
    4. Return computed result

    Usage:
        evaluator = ComputedFieldEvaluator()
        result = evaluator.evaluate(
            formula="nominal_rate * 100",
            values={"nominal_rate": 0.05},
            depends_on=["nominal_rate"]
        )
        print(result)  # 5.0
    """

    def __init__(self) -> None:
        """Initialize evaluator."""
        self._safe_globals = {
            "__builtins__": {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "len": len,
                "pow": pow,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
            }
        }

    def evaluate(
        self,
        formula: str,
        values: dict[str, Any],
        depends_on: Optional[list[str]] = None
    ) -> Any:
        """
        Evaluate formula với provided values.

        Args:
            formula: Formula string (Python expression)
            values: Map của field names → values
            depends_on: List of field names mà formula phụ thuộc

        Returns:
            Computed value

        Raises:
            FormulaError: Nếu formula evaluation thất bại
            ValueError: Nếu missing dependency
        """
        # Validate dependencies
        if depends_on:
            missing = [dep for dep in depends_on if dep not in values]
            if missing:
                raise FormulaError(
                    field_name="",
                    formula=formula,
                    message=f"Missing dependencies: {', '.join(missing)}",
                )

        # Build local namespace từ values
        local_ns = values.copy()

        try:
            # Evaluate formula
            result = eval(formula, self._safe_globals, local_ns)
            return result
        except Exception as e:
            raise FormulaError(
                field_name="",
                formula=formula,
                message=str(e),
                cause=e,
            )

    def evaluate_field(
        self,
        field_type: str,
        formula: str,
        values: dict[str, Any],
        depends_on: Optional[list[str]] = None
    ) -> Any:
        """
        Evaluate computed field với type coercion.

        Args:
            field_type: Expected field type
            formula: Formula string
            values: Field values
            depends_on: Dependencies

        Returns:
            Computed value với correct type

        Raises:
            FormulaError: Nếu evaluation hoặc coercion thất bại
        """
        result = self.evaluate(formula, values, depends_on)

        # Type coercion
        try:
            if field_type in ("decimal",):
                from decimal import Decimal
                return Decimal(str(result))
            elif field_type in ("integer", "int"):
                return int(result)
            elif field_type in ("float",):
                return float(result)
            elif field_type in ("boolean", "bool"):
                return bool(result)
            elif field_type in ("string", "str"):
                return str(result)
            else:
                return result
        except Exception as e:
            raise FormulaError(
                field_name="",
                formula=formula,
                message=f"Type coercion failed for type {field_type}: {e}",
                cause=e,
            )

    def generate_python_code(
        self,
        field_name: str,
        field_type: str,
        formula: str,
        depends_on: list[str]
    ) -> str:
        """
        Generate Python property code cho computed field.

        Args:
            field_name: Field name
            field_type: Field type
            formula: Formula
            depends_on: Dependencies

        Returns:
            Python property code
        """
        # Type coercion
        type_coerce = ""
        if field_type in ("decimal",):
            type_coerce = "Decimal(str("
            formula = f"{formula})"
        elif field_type in ("integer", "int"):
            type_coerce = "int("
        elif field_type in ("float",):
            type_coerce = "float("

        if type_coerce:
            return_type = self._get_python_type(field_type)
            code = f"""
    @property
    def {field_name}(self) -> {return_type}:
        \"\"\"Computed field: {field_name}\"\"\"
        return {type_coerce}{formula})"""
        else:
            code = f"""
    @property
    def {field_name}(self) -> Any:
        \"\"\"Computed field: {field_name}\"\"\"
        return {formula}"""

        return code

    def generate_typescript_code(
        self,
        field_name: str,
        field_type: str,
        formula: str,
        depends_on: list[str]
    ) -> str:
        """
        Generate TypeScript getter code cho computed field.

        Args:
            field_name: Field name
            field_type: Field type
            formula: Formula
            depends_on: Dependencies

        Returns:
            TypeScript getter code
        """
        return_type = self._get_typescript_type(field_type)

        # Convert Python formula to TypeScript
        ts_formula = self._convert_to_typescript(formula)

        code = f"""
    get {field_name}(): {return_type} {{
        // Computed field: {field_name}
        return {ts_formula};
    }}"""

        return code

    def _convert_to_typescript(self, formula: str) -> str:
        """
        Convert Python formula to TypeScript.

        Args:
            formula: Python formula

        Returns:
            TypeScript formula
        """
        # Basic conversions
        ts_formula = formula

        # Python ** → TypeScript **
        # (already compatible)

        # Python True/False → TypeScript true/false
        ts_formula = ts_formula.replace("True", "true").replace("False", "false")

        # Python None → TypeScript null/undefined
        ts_formula = ts_formula.replace("None", "null")

        return ts_formula

    def _get_python_type(self, field_type: str) -> str:
        """
        Get Python type annotation.

        Args:
            field_type: Field type

        Returns:
            Type annotation string
        """
        type_map = {
            "string": "str",
            "str": "str",
            "integer": "int",
            "int": "int",
            "decimal": "Decimal",
            "float": "float",
            "boolean": "bool",
            "bool": "bool",
            "datetime": "datetime",
        }
        return type_map.get(field_type, "Any")

    def _get_typescript_type(self, field_type: str) -> str:
        """
        Get TypeScript type annotation.

        Args:
            field_type: Field type

        Returns:
            Type annotation string
        """
        type_map = {
            "string": "string",
            "str": "string",
            "integer": "number",
            "int": "number",
            "decimal": "number",
            "float": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "datetime": "Date",
        }
        return type_map.get(field_type, "any")

    def validate_formula(
        self,
        formula: str,
        depends_on: list[str]
    ) -> tuple[bool, str]:
        """
        Validate formula syntax.

        Args:
            formula: Formula string
            depends_on: Dependencies

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Build test namespace
        test_ns = {dep: 0 for dep in depends_on}

        try:
            # Try to compile formula
            compile(formula, "<string>", "eval")

            # Try to evaluate with test values
            eval(formula, self._safe_globals, test_ns)

            return True, ""
        except Exception as e:
            return False, str(e)

    def get_field_dependencies(
        self,
        formula: str
    ) -> list[str]:
        """
        Extract field dependencies từ formula.

        Args:
            formula: Formula string

        Returns:
            List of field names used in formula
        """
        import re

        # Find all identifiers (field names)
        identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', formula)

        # Filter out Python keywords và builtins
        keywords = {
            'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is',
            'abs', 'round', 'min', 'max', 'sum', 'len', 'pow',
            'int', 'float', 'str', 'bool',
        }

        return [id for id in identifiers if id not in keywords]