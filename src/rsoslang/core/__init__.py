"""RSOS Core: the technical layer of RSOS.

Neutral operation names, one compiled form (the IR), a deterministic runtime, stable error codes and a state digest.
The symbolic RSOS language compiles to Core; nothing in Core imports the symbolic layer.

    from rsoslang.core import compile_rsos, parse_core, execute_ir, ir_digest, state_digest, Ledger

Specification: spec/core/STATE_OPS.md (Core v1).
"""
from rsoslang.core.ir import (CORE_OPS, CORE_VERSION, compile_rsos, execute_ir, from_ir, ir_digest, parse_core,
                              to_core_text, to_ir)
from rsoslang.core.state import GRAMMAR, Ledger, OpError, dot, execute, parse_ops, parse_plan, plan_prompt

state_digest = dot
"""Core name of the green dot: the first 12 hex digits of SHA-256 over the state's canonical JSON."""

__all__ = ["CORE_OPS", "CORE_VERSION", "GRAMMAR", "Ledger", "OpError", "compile_rsos", "dot", "execute",
           "execute_ir", "from_ir", "ir_digest", "parse_core", "parse_ops", "parse_plan", "plan_prompt",
           "state_digest", "to_core_text", "to_ir"]
