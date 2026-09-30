"""
JOCKY Compiler — Semantic Analyzer
Validates AST for type correctness and semantic rules.
"""
from typing import List
from compiler.ast_nodes import (
    ASTVisitor, Program, InvestigationBlock, HostBlock,
    CollectStatement, AnalyzeStatement, FilterStatement, GenerateStatement,
    BinaryOp, Identifier,
)

ANALYZABLE_TARGETS = {"PROCESSES", "NETWORK_CONNECTIONS", "PERSISTENCE", "EVENT_LOGS", "FILESYSTEM"}
FILTERABLE_TARGETS = {"PROCESSES", "NETWORK_CONNECTIONS", "EVENT_LOGS", "PERSISTENCE"}

FILTER_FIELDS = {
    "PROCESSES": {"cpu", "memory", "pid", "name", "path", "username", "status"},
    "NETWORK_CONNECTIONS": {"port", "remote_address", "local_address", "protocol", "state", "process_name"},
    "EVENT_LOGS": {"severity", "source", "event_id", "message"},
    "PERSISTENCE": {"category", "location", "name", "enabled"},
}

VALID_OPS = {">", "<", ">=", "<=", "==", "!=", "in"}


class SemanticError(Exception):
    pass


class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._collected: set = set()
        self._scope: str = "global"

    def analyze(self, program: Program) -> bool:
        self.visit(program)
        return len(self.errors) == 0

    def _error(self, msg: str, node=None):
        loc = f" [{node.loc}]" if node and node.loc else ""
        self.errors.append(f"SemanticError{loc}: {msg}")

    def _warn(self, msg: str, node=None):
        loc = f" [{node.loc}]" if node and node.loc else ""
        self.warnings.append(f"Warning{loc}: {msg}")

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_InvestigationBlock(self, node: InvestigationBlock):
        if not node.name.strip():
            self._error("Investigation name cannot be empty", node)
        prev_scope = self._scope
        self._scope = f"investigation:{node.name}"
        prev_collected = self._collected.copy()
        self._collected = set()
        for stmt in node.body:
            self.visit(stmt)
        self._check_generate_dependencies(node.body, node)
        self._collected = prev_collected
        self._scope = prev_scope

    def visit_HostBlock(self, node: HostBlock):
        if not node.name.strip():
            self._error("Host name cannot be empty", node)
        prev_scope = self._scope
        self._scope = f"host:{node.name}"
        prev_collected = self._collected.copy()
        self._collected = set()
        for stmt in node.body:
            self.visit(stmt)
        self._collected = prev_collected
        self._scope = prev_scope

    def visit_CollectStatement(self, node: CollectStatement):
        if node.target in self._collected:
            self._warn(f"'{node.target}' collected more than once in this scope", node)
        self._collected.add(node.target)

    def visit_AnalyzeStatement(self, node: AnalyzeStatement):
        if node.target not in ANALYZABLE_TARGETS:
            self._error(f"'{node.target}' is not analyzable. Valid targets: {ANALYZABLE_TARGETS}", node)
        if node.target not in self._collected:
            self._warn(f"Analyzing '{node.target}' without collecting it first", node)

    def visit_FilterStatement(self, node: FilterStatement):
        if node.target not in FILTERABLE_TARGETS:
            self._error(f"'{node.target}' is not filterable. Valid targets: {FILTERABLE_TARGETS}", node)
        if node.target not in self._collected:
            self._warn(f"Filtering '{node.target}' without collecting it first", node)
        if node.condition:
            self._validate_condition(node.condition, node.target, node)

    def _validate_condition(self, cond: BinaryOp, target: str, node):
        if not isinstance(cond.left, Identifier):
            self._error("Filter condition left side must be a field name", node)
            return
        field = cond.left.name
        valid_fields = FILTER_FIELDS.get(target, set())
        if valid_fields and field not in valid_fields:
            self._warn(f"Field '{field}' is not a known field for {target}. Valid: {valid_fields}", node)
        if cond.op not in VALID_OPS:
            self._error(f"Invalid operator '{cond.op}'. Valid: {VALID_OPS}", node)

    def visit_GenerateStatement(self, node: GenerateStatement):
        pass  # generate is always valid

    def _check_generate_dependencies(self, body, node):
        has_generate = any(isinstance(s, GenerateStatement) for s in body)
        has_collect = any(isinstance(s, CollectStatement) for s in body)
        if has_generate and not has_collect:
            self._warn("Generating output without any collect statements — results may be empty", node)
