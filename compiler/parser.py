"""
JOCKY Compiler — Recursive-Descent Parser
Parses token stream → AST using the JOCKY grammar.
"""
from typing import List, Optional

from compiler.lexer import Token, TokenType, COLLECTOR_TOKENS
from compiler.ast_nodes import (
    Program, InvestigationBlock, HostBlock,
    CollectStatement, AnalyzeStatement, FilterStatement, GenerateStatement,
    BinaryOp, StringLiteral, IntLiteral, FloatLiteral, Identifier, ListLiteral,
    SourceLocation,
)

GENERATE_TARGETS = {TokenType.TIMELINE, TokenType.REPORT}

# Map token types → canonical target names
TARGET_MAP = {
    TokenType.PROCESSES: "PROCESSES",
    TokenType.NETWORK_CONNECTIONS: "NETWORK_CONNECTIONS",
    TokenType.SYSTEM_INFO: "SYSTEM_INFO",
    TokenType.EVENT_LOGS: "EVENT_LOGS",
    TokenType.PERSISTENCE: "PERSISTENCE",
    TokenType.FILESYSTEM: "FILESYSTEM",
    TokenType.STARTUP_ITEMS: "STARTUP_ITEMS",
    TokenType.BROWSER_ARTIFACTS: "BROWSER_ARTIFACTS",
    TokenType.HASHES: "HASHES",
    TokenType.TIMELINE: "TIMELINE",
    TokenType.REPORT: "REPORT",
}


class ParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        loc = f" at L{token.line}:C{token.col}" if token else ""
        super().__init__(f"ParseError{loc}: {message}")
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        return self.tokens[min(idx, len(self.tokens) - 1)]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def check(self, *types: TokenType) -> bool:
        return self.peek().type in types

    def expect(self, *types: TokenType) -> Token:
        if self.check(*types):
            return self.advance()
        tok = self.peek()
        raise ParseError(
            f"Expected {[t.name for t in types]}, got {tok.type.name} ({tok.value!r})", tok
        )

    def loc(self) -> SourceLocation:
        t = self.peek()
        return SourceLocation(t.line, t.col)

    def parse(self) -> Program:
        stmts = []
        while not self.check(TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return Program(statements=stmts)

    def parse_statement(self):
        tok = self.peek()

        if tok.type == TokenType.INVESTIGATION:
            return self.parse_investigation()
        elif tok.type == TokenType.HOST:
            return self.parse_host()
        elif tok.type == TokenType.COLLECT:
            return self.parse_collect()
        elif tok.type == TokenType.ANALYZE:
            return self.parse_analyze()
        elif tok.type == TokenType.FILTER:
            return self.parse_filter()
        elif tok.type == TokenType.GENERATE:
            return self.parse_generate()
        elif tok.type == TokenType.EOF:
            return None
        else:
            raise ParseError(f"Unexpected token: {tok.type.name} ({tok.value!r})", tok)

    def parse_investigation(self) -> InvestigationBlock:
        loc = self.loc()
        self.expect(TokenType.INVESTIGATION)
        name_tok = self.expect(TokenType.STRING)
        self.expect(TokenType.LBRACE)
        body = self.parse_body()
        self.expect(TokenType.RBRACE)
        return InvestigationBlock(name=name_tok.value, body=body, loc=loc)

    def parse_host(self) -> HostBlock:
        loc = self.loc()
        self.expect(TokenType.HOST)
        name_tok = self.expect(TokenType.STRING)
        self.expect(TokenType.LBRACE)
        body = self.parse_body()
        self.expect(TokenType.RBRACE)
        return HostBlock(name=name_tok.value, body=body, loc=loc)

    def parse_body(self):
        stmts = []
        while not self.check(TokenType.RBRACE, TokenType.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        return stmts

    def parse_collect(self) -> CollectStatement:
        loc = self.loc()
        self.expect(TokenType.COLLECT)
        target_tok = self.peek()
        if target_tok.type not in COLLECTOR_TOKENS:
            raise ParseError(
                f"Expected a collector target (processes, network_connections, etc.), got {target_tok.value!r}",
                target_tok
            )
        self.advance()
        return CollectStatement(target=TARGET_MAP[target_tok.type], loc=loc)

    def parse_analyze(self) -> AnalyzeStatement:
        loc = self.loc()
        self.expect(TokenType.ANALYZE)
        target_tok = self.peek()
        if target_tok.type not in COLLECTOR_TOKENS:
            raise ParseError(f"Expected analyzable target, got {target_tok.value!r}", target_tok)
        self.advance()
        return AnalyzeStatement(target=TARGET_MAP[target_tok.type], loc=loc)

    def parse_filter(self) -> FilterStatement:
        loc = self.loc()
        self.expect(TokenType.FILTER)
        target_tok = self.peek()
        if target_tok.type not in COLLECTOR_TOKENS:
            raise ParseError(f"Expected filterable target, got {target_tok.value!r}", target_tok)
        self.advance()
        target = TARGET_MAP[target_tok.type]

        condition = None
        if self.check(TokenType.WHERE):
            self.advance()  # consume 'where'
            condition = self.parse_condition()

        return FilterStatement(target=target, condition=condition, loc=loc)

    def parse_condition(self):
        """Parse: <field> <op> <value>  |  <field> in [...]"""
        left_tok = self.advance()  # field identifier
        left = Identifier(name=left_tok.value, loc=SourceLocation(left_tok.line, left_tok.col))

        op_tok = self.advance()
        op = op_tok.value

        if op_tok.type == TokenType.IN:
            # field in [val, val, ...]
            self.expect(TokenType.LBRACKET)
            elements = []
            while not self.check(TokenType.RBRACKET, TokenType.EOF):
                elements.append(self._parse_value())
                if self.check(TokenType.COMMA):
                    self.advance()
            self.expect(TokenType.RBRACKET)
            right = ListLiteral(elements=elements)
        else:
            right = self._parse_value()

        return BinaryOp(op=op, left=left, right=right)

    def _parse_value(self):
        tok = self.advance()
        if tok.type == TokenType.STRING:
            return StringLiteral(value=tok.value)
        elif tok.type == TokenType.INTEGER:
            return IntLiteral(value=int(tok.value))
        elif tok.type == TokenType.FLOAT:
            return FloatLiteral(value=float(tok.value))
        elif tok.type == TokenType.BOOLEAN:
            return BoolLiteral(value=tok.value == "true")
        elif tok.type == TokenType.IDENTIFIER:
            return Identifier(name=tok.value)
        else:
            raise ParseError(f"Expected value, got {tok.type.name}", tok)

    def parse_generate(self) -> GenerateStatement:
        loc = self.loc()
        self.expect(TokenType.GENERATE)
        target_tok = self.peek()
        if target_tok.type not in GENERATE_TARGETS:
            raise ParseError(
                f"Expected 'timeline' or 'report', got {target_tok.value!r}", target_tok
            )
        self.advance()
        return GenerateStatement(what=TARGET_MAP[target_tok.type], loc=loc)
