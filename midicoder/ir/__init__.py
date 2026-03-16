"""IR module for Midicoder."""

from .builder import build_ir
from .diagnostics import CompilerError, ErrorReporter
from .symbols import Symbol, SymbolTable
from .validation import Validator, CrossRefChecker
from .normalize import Normalizer

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
