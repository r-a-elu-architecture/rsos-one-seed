"""RSOS Language: a spatial-symbolic programming language for humans and AI.

One program, two runtimes: an AI system and a person's practised mental model.
The core (fixed meanings), declared bindings (scoped variations) and search (meanings left open
on purpose) follow decision D80 and addition T12 of the corpus.
"""

from .lexer import tokenize
from .parser import parse, Program
from .compiler import compile_source, compile_file
from .diagnostics import Diagnostic

__version__ = "0.4.0"
LANGUAGE_VERSION = "0.2"

__all__ = ["tokenize", "parse", "Program", "compile_source", "compile_file", "Diagnostic",
           "__version__", "LANGUAGE_VERSION"]
