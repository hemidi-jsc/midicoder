"""IR module for Midicoder."""

from .builder import build_ir
from .diagnostics import CompilerError, ErrorReporter
from .normalize import Normalizer
from .symbols import Symbol, SymbolTable
from .validation import CrossRefChecker, Validator

__all__ = [
    "build_ir",
    "CompilerError",
    "ErrorReporter",
    "Symbol",
    "SymbolTable",
    "Validator",
    "CrossRefChecker",
    "Normalizer",
]
