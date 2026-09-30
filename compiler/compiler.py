"""
JOCKY Compiler — Main Orchestrator
Lexer → Parser → AST → Semantic → IR → Transform → Build
"""
import json
import hashlib
import time
import traceback
from typing import Optional

from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParseError
from compiler.semantic import SemanticAnalyzer, SemanticError
from compiler.ir import IRBuilder
from compiler.transformers import ProfileSelector


class JockyCompiler:
    """Public API for the JOCKY compiler pipeline."""

    def validate(self, source_code: str) -> dict:
        """Run lexer → parser → semantic analysis. Returns structured result."""
        steps = []
        errors = []
        warnings = []

        # Step 1: Lex
        try:
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            steps.append({"step": "Lexer", "status": "ok",
                          "detail": f"{len(tokens)-1} tokens produced"})
        except LexerError as e:
            steps.append({"step": "Lexer", "status": "error", "detail": str(e)})
            errors.append(str(e))
            return {"valid": False, "steps": steps, "errors": errors, "warnings": warnings}

        # Step 2: Parse
        try:
            parser = Parser(tokens)
            ast = parser.parse()
            stmt_count = len(ast.statements)
            steps.append({"step": "Parser", "status": "ok",
                          "detail": f"AST: {stmt_count} top-level statement(s)"})
        except ParseError as e:
            steps.append({"step": "Parser", "status": "error", "detail": str(e)})
            errors.append(str(e))
            return {"valid": False, "steps": steps, "errors": errors, "warnings": warnings}

        # Step 3: Semantic
        analyzer = SemanticAnalyzer()
        is_valid = analyzer.analyze(ast)
        warnings.extend(analyzer.warnings)

        if is_valid:
            steps.append({"step": "Semantic Analysis", "status": "ok",
                          "detail": f"{len(analyzer.warnings)} warning(s)"})
        else:
            steps.append({"step": "Semantic Analysis", "status": "error",
                          "detail": f"{len(analyzer.errors)} error(s)"})
            errors.extend(analyzer.errors)
            return {"valid": False, "steps": steps, "errors": errors, "warnings": warnings}

        return {"valid": True, "steps": steps, "errors": [], "warnings": warnings}

    def compile(self, source_code: str) -> dict:
        """Full compile: lex → parse → semantic → IR. Returns IR + validation."""
        t0 = time.time()
        result = self.validate(source_code)

        if not result["valid"]:
            return {**result, "success": False, "ir": None, "ast_summary": None}

        # Build IR
        try:
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            builder = IRBuilder(source=source_code)
            ir = builder.build(ast)

            # AST summary for UI display
            ast_summary = self._summarize_ast(ast)

            ir_dict = ir.to_dict()
            elapsed_ms = (time.time() - t0) * 1000

            result["steps"].append({"step": "IR Generation", "status": "ok",
                                    "detail": f"{ir.node_count()} IR nodes in {ir_dict.get('scopes', []).__len__()} scope(s)"})
            return {
                "success": True,
                "valid": True,
                "steps": result["steps"],
                "errors": [],
                "warnings": result["warnings"],
                "ir": ir_dict,
                "ir_node_count": ir.node_count(),
                "ast_summary": ast_summary,
                "compile_time_ms": round(elapsed_ms, 2),
            }
        except Exception as e:
            return {
                "success": False, "valid": False,
                "steps": result["steps"],
                "errors": [f"IR generation failed: {e}"],
                "warnings": result["warnings"],
                "ir": None,
            }

    def build(self, source_code: str, profile: str = "forensic_standard") -> dict:
        """Full build with transformation pipeline applied."""
        compile_result = self.compile(source_code)
        if not compile_result.get("success"):
            return compile_result

        try:
            # Rebuild IR object for transformation
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            builder = IRBuilder(source=source_code)
            ir = builder.build(ast)

            # Apply transformation pipeline
            selector = ProfileSelector(profile)
            transformed_ir, transformation_log = selector.apply(ir)

            ir_dict = transformed_ir.to_dict()
            ir_json = json.dumps(ir_dict, sort_keys=True)
            sha256 = hashlib.sha256(ir_json.encode() + profile.encode()).hexdigest()

            return {
                **compile_result,
                "success": True,
                "ir": ir_dict,
                "ir_node_count": transformed_ir.node_count(),
                "sha256": sha256,
                "profile": profile,
                "transformations": transformation_log,
                "metadata": {
                    "profile": profile,
                    "ir_version": transformed_ir.version,
                    "scope_count": len(transformed_ir.scopes),
                    "total_ops": transformed_ir.node_count(),
                },
            }
        except Exception as e:
            return {
                **compile_result,
                "success": False,
                "errors": compile_result.get("errors", []) + [f"Build failed: {e}"],
                "traceback": traceback.format_exc(),
            }

    def _summarize_ast(self, ast) -> dict:
        """Build a JSON-serializable summary of the AST for UI display."""
        from compiler.ast_nodes import (
            InvestigationBlock, HostBlock, CollectStatement,
            AnalyzeStatement, FilterStatement, GenerateStatement
        )
        summary = {"node_type": "Program", "children": []}
        for stmt in ast.statements:
            if isinstance(stmt, InvestigationBlock):
                child = {"node_type": "InvestigationBlock", "name": stmt.name, "children": []}
                for s in stmt.body:
                    child["children"].append(self._stmt_summary(s))
                summary["children"].append(child)
            elif isinstance(stmt, HostBlock):
                child = {"node_type": "HostBlock", "name": stmt.name, "children": []}
                for s in stmt.body:
                    child["children"].append(self._stmt_summary(s))
                summary["children"].append(child)
            else:
                summary["children"].append(self._stmt_summary(stmt))
        return summary

    def _stmt_summary(self, stmt) -> dict:
        from compiler.ast_nodes import (
            CollectStatement, AnalyzeStatement, FilterStatement, GenerateStatement
        )
        if isinstance(stmt, CollectStatement):
            return {"node_type": "CollectStatement", "target": stmt.target}
        elif isinstance(stmt, AnalyzeStatement):
            return {"node_type": "AnalyzeStatement", "target": stmt.target}
        elif isinstance(stmt, FilterStatement):
            return {"node_type": "FilterStatement", "target": stmt.target,
                    "has_condition": stmt.condition is not None}
        elif isinstance(stmt, GenerateStatement):
            return {"node_type": "GenerateStatement", "what": stmt.what}
        return {"node_type": stmt.__class__.__name__}
