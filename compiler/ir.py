"""
JOCKY Compiler — Intermediate Representation (IR)
Custom IR that is backend-independent and transformation-ready.
Designed for future LLVM backend attachment.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from compiler.ast_nodes import (
    ASTVisitor, Program, InvestigationBlock, HostBlock,
    CollectStatement, AnalyzeStatement, FilterStatement, GenerateStatement,
    BinaryOp, Identifier, ListLiteral, StringLiteral, IntLiteral, FloatLiteral,
)


# ── IR Opcodes ────────────────────────────────────────────────────────

class OpCode:
    # Collection
    COLLECT = "COLLECT"
    # Analysis
    ANALYZE = "ANALYZE"
    # Filtering
    FILTER = "FILTER"
    # Generation
    GENERATE_TIMELINE = "GENERATE_TIMELINE"
    GENERATE_REPORT = "GENERATE_REPORT"
    # Flow
    BEGIN_SCOPE = "BEGIN_SCOPE"
    END_SCOPE = "END_SCOPE"
    # Metadata
    META = "META"


# ── IR Node ───────────────────────────────────────────────────────────

@dataclass
class IRNode:
    """A single IR operation node."""
    op: str                              # OpCode
    target: Optional[str] = None         # Primary target (PROCESSES, NETWORK_CONNECTIONS…)
    arguments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_location: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "op": self.op,
            "target": self.target,
            "arguments": self.arguments,
            "metadata": self.metadata,
            "source_location": self.source_location,
        }


@dataclass
class IRScope:
    """Represents investigation or host scope."""
    scope_type: str    # "investigation" | "host"
    name: str
    operations: List[IRNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scope_type": self.scope_type,
            "name": self.name,
            "operations": [op.to_dict() for op in self.operations],
        }


@dataclass
class IRProgram:
    """Root IR object."""
    version: str = "1.0"
    scopes: List[IRScope] = field(default_factory=list)
    global_ops: List[IRNode] = field(default_factory=list)
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "type": "ir_program",
            "scopes": [s.to_dict() for s in self.scopes],
            "global_ops": [op.to_dict() for op in self.global_ops],
            "_source": self.source or "",
        }

    def all_operations(self) -> List[IRNode]:
        ops = list(self.global_ops)
        for scope in self.scopes:
            ops.extend(scope.operations)
        return ops

    def node_count(self) -> int:
        return len(self.all_operations())


# ── IR Builder (AST → IR) ─────────────────────────────────────────────

def _serialize_condition(cond) -> Optional[dict]:
    if cond is None:
        return None
    if isinstance(cond, BinaryOp):
        return {
            "op": cond.op,
            "left": _serialize_condition(cond.left),
            "right": _serialize_condition(cond.right),
        }
    if isinstance(cond, Identifier):
        return {"type": "identifier", "name": cond.name}
    if isinstance(cond, (IntLiteral, FloatLiteral)):
        return {"type": "literal", "value": cond.value}
    if isinstance(cond, StringLiteral):
        return {"type": "literal", "value": cond.value}
    if isinstance(cond, ListLiteral):
        return {"type": "list", "elements": [_serialize_condition(e) for e in cond.elements]}
    return {"type": "unknown", "value": str(cond)}


class IRBuilder(ASTVisitor):
    def __init__(self, source: str = ""):
        self._source = source
        self._ir = IRProgram(source=source)
        self._current_scope: Optional[IRScope] = None

    def build(self, program: Program) -> IRProgram:
        self.visit(program)
        return self._ir

    def _emit(self, node: IRNode):
        if self._current_scope is not None:
            self._current_scope.operations.append(node)
        else:
            self._ir.global_ops.append(node)

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_InvestigationBlock(self, node: InvestigationBlock):
        scope = IRScope(scope_type="investigation", name=node.name)
        prev = self._current_scope
        self._current_scope = scope
        for stmt in node.body:
            self.visit(stmt)
        self._current_scope = prev
        self._ir.scopes.append(scope)

    def visit_HostBlock(self, node: HostBlock):
        scope = IRScope(scope_type="host", name=node.name)
        prev = self._current_scope
        self._current_scope = scope
        for stmt in node.body:
            self.visit(stmt)
        self._current_scope = prev
        self._ir.scopes.append(scope)

    def visit_CollectStatement(self, node: CollectStatement):
        loc = str(node.loc) if node.loc else None
        self._emit(IRNode(op=OpCode.COLLECT, target=node.target, source_location=loc))

    def visit_AnalyzeStatement(self, node: AnalyzeStatement):
        loc = str(node.loc) if node.loc else None
        self._emit(IRNode(op=OpCode.ANALYZE, target=node.target, source_location=loc))

    def visit_FilterStatement(self, node: FilterStatement):
        loc = str(node.loc) if node.loc else None
        args = {}
        if node.condition:
            args["condition"] = _serialize_condition(node.condition)
        self._emit(IRNode(op=OpCode.FILTER, target=node.target, arguments=args, source_location=loc))

    def visit_GenerateStatement(self, node: GenerateStatement):
        loc = str(node.loc) if node.loc else None
        op = OpCode.GENERATE_TIMELINE if node.what == "TIMELINE" else OpCode.GENERATE_REPORT
        self._emit(IRNode(op=op, source_location=loc))
