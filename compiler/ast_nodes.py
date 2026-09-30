"""
JOCKY Compiler — AST Node Definitions
All AST nodes use Python dataclasses for clean, inspectable representation.
Field ordering: required fields BEFORE fields with defaults.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class SourceLocation:
    line: int
    col: int

    def __repr__(self):
        return f"L{self.line}:C{self.col}"


# ── Marker class (not a dataclass to avoid field ordering issues) ──────

class ASTNode:
    """Base marker for all JOCKY AST nodes."""
    def node_type(self) -> str:
        return self.__class__.__name__


# ── Expressions ───────────────────────────────────────────────────────

@dataclass
class StringLiteral(ASTNode):
    value: str
    loc: Optional[SourceLocation] = None


@dataclass
class IntLiteral(ASTNode):
    value: int
    loc: Optional[SourceLocation] = None


@dataclass
class FloatLiteral(ASTNode):
    value: float
    loc: Optional[SourceLocation] = None


@dataclass
class BoolLiteral(ASTNode):
    value: bool
    loc: Optional[SourceLocation] = None


@dataclass
class Identifier(ASTNode):
    name: str
    loc: Optional[SourceLocation] = None


@dataclass
class ListLiteral(ASTNode):
    elements: List[Any] = field(default_factory=list)
    loc: Optional[SourceLocation] = None


@dataclass
class BinaryOp(ASTNode):
    op: str = ''
    left: Any = None
    right: Any = None
    loc: Optional[SourceLocation] = None


# ── Statements ────────────────────────────────────────────────────────

@dataclass
class CollectStatement(ASTNode):
    """collect <target>"""
    target: str = ''
    loc: Optional[SourceLocation] = None


@dataclass
class AnalyzeStatement(ASTNode):
    """analyze <target>"""
    target: str = ''
    loc: Optional[SourceLocation] = None


@dataclass
class FilterStatement(ASTNode):
    """filter <target> where <condition>"""
    target: str = ''
    condition: Optional[BinaryOp] = None
    loc: Optional[SourceLocation] = None


@dataclass
class GenerateStatement(ASTNode):
    """generate <what>"""
    what: str = ''
    loc: Optional[SourceLocation] = None


@dataclass
class InvestigationBlock(ASTNode):
    """investigation \"Name\" { ... }"""
    name: str = ''
    body: List[ASTNode] = field(default_factory=list)
    loc: Optional[SourceLocation] = None


@dataclass
class HostBlock(ASTNode):
    """host \"Name\" { ... }"""
    name: str = ''
    body: List[ASTNode] = field(default_factory=list)
    loc: Optional[SourceLocation] = None


@dataclass
class Program(ASTNode):
    """Root AST node — list of top-level statements."""
    statements: List[ASTNode] = field(default_factory=list)
    loc: Optional[SourceLocation] = None


# ── Visitor base ──────────────────────────────────────────────────────

class ASTVisitor:
    """Base visitor — subclass and override visit_* methods."""

    def visit(self, node: ASTNode):
        method = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        pass


class ASTPrinter(ASTVisitor):
    """Debug printer for AST inspection."""

    def __init__(self):
        self.indent = 0

    def _p(self, text: str):
        print("  " * self.indent + text)

    def visit_Program(self, node: Program):
        self._p(f"Program ({len(node.statements)} statements)")
        self.indent += 1
        for s in node.statements:
            self.visit(s)
        self.indent -= 1

    def visit_InvestigationBlock(self, node: InvestigationBlock):
        self._p(f"Investigation: \"{node.name}\"")
        self.indent += 1
        for s in node.body:
            self.visit(s)
        self.indent -= 1

    def visit_HostBlock(self, node: HostBlock):
        self._p(f"Host: \"{node.name}\"")
        self.indent += 1
        for s in node.body:
            self.visit(s)
        self.indent -= 1

    def visit_CollectStatement(self, node: CollectStatement):
        self._p(f"Collect: {node.target}")

    def visit_AnalyzeStatement(self, node: AnalyzeStatement):
        self._p(f"Analyze: {node.target}")

    def visit_FilterStatement(self, node: FilterStatement):
        self._p(f"Filter: {node.target} where {node.condition}")

    def visit_GenerateStatement(self, node: GenerateStatement):
        self._p(f"Generate: {node.what}")
