"""
JOCKY Compiler — Lexer
Tokenizes JOCKY source code into a stream of tokens.
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    # Keywords
    INVESTIGATION = auto()
    HOST = auto()
    COLLECT = auto()
    ANALYZE = auto()
    FILTER = auto()
    GENERATE = auto()
    WHERE = auto()
    IN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Collector targets
    PROCESSES = auto()
    NETWORK_CONNECTIONS = auto()
    SYSTEM_INFO = auto()
    EVENT_LOGS = auto()
    PERSISTENCE = auto()
    FILESYSTEM = auto()
    STARTUP_ITEMS = auto()
    BROWSER_ARTIFACTS = auto()
    HASHES = auto()

    # Generate targets
    TIMELINE = auto()
    REPORT = auto()

    # Literals
    STRING = auto()       # "..."
    INTEGER = auto()      # 42
    FLOAT = auto()        # 3.14
    IDENTIFIER = auto()   # user-defined name
    BOOLEAN = auto()      # true / false

    # Operators / punctuation
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    LBRACKET = auto()     # [
    RBRACKET = auto()     # ]
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    COMMA = auto()        # ,
    DOT = auto()          # .
    SEMICOLON = auto()    # ;
    GT = auto()           # >
    LT = auto()           # <
    GTE = auto()          # >=
    LTE = auto()          # <=
    EQ = auto()           # ==
    NEQ = auto()          # !=
    ASSIGN = auto()       # =

    # Misc
    NEWLINE = auto()
    EOF = auto()
    COMMENT = auto()      # // or #


KEYWORDS = {
    "investigation": TokenType.INVESTIGATION,
    "host": TokenType.HOST,
    "collect": TokenType.COLLECT,
    "analyze": TokenType.ANALYZE,
    "filter": TokenType.FILTER,
    "generate": TokenType.GENERATE,
    "where": TokenType.WHERE,
    "in": TokenType.IN,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.BOOLEAN,
    "false": TokenType.BOOLEAN,
    # Collector names
    "processes": TokenType.PROCESSES,
    "network_connections": TokenType.NETWORK_CONNECTIONS,
    "system_info": TokenType.SYSTEM_INFO,
    "event_logs": TokenType.EVENT_LOGS,
    "persistence": TokenType.PERSISTENCE,
    "filesystem": TokenType.FILESYSTEM,
    "startup_items": TokenType.STARTUP_ITEMS,
    "browser_artifacts": TokenType.BROWSER_ARTIFACTS,
    "hashes": TokenType.HASHES,
    # Generate targets
    "timeline": TokenType.TIMELINE,
    "report": TokenType.REPORT,
}

COLLECTOR_TOKENS = {
    TokenType.PROCESSES, TokenType.NETWORK_CONNECTIONS, TokenType.SYSTEM_INFO,
    TokenType.EVENT_LOGS, TokenType.PERSISTENCE, TokenType.FILESYSTEM,
    TokenType.STARTUP_ITEMS, TokenType.BROWSER_ARTIFACTS, TokenType.HASHES,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.col})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"LexerError at L{line}:C{col}: {message}")
        self.line = line
        self.col = col


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def error(self, msg: str) -> LexerError:
        return LexerError(msg, self.line, self.col)

    def peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def skip_whitespace(self):
        while self.pos < len(self.source) and self.peek() in (" ", "\t", "\r"):
            self.advance()

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # opening "
        buf = []
        while self.pos < len(self.source):
            ch = self.peek()
            if ch == "\\":
                self.advance()
                esc = self.advance()
                buf.append({"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}.get(esc, esc))
            elif ch == '"':
                self.advance()  # closing "
                return Token(TokenType.STRING, "".join(buf), start_line, start_col)
            elif ch == "\n":
                raise self.error("Unterminated string literal")
            else:
                buf.append(self.advance())
        raise self.error("Unterminated string literal at EOF")

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        buf = []
        is_float = False
        while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == "."):
            ch = self.advance()
            if ch == ".":
                is_float = True
            buf.append(ch)
        val = "".join(buf)
        return Token(TokenType.FLOAT if is_float else TokenType.INTEGER, val, start_line, start_col)

    def read_identifier(self) -> Token:
        start_line, start_col = self.line, self.col
        buf = []
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() in ("_", "-")):
            buf.append(self.advance())
        word = "".join(buf)
        ttype = KEYWORDS.get(word, TokenType.IDENTIFIER)
        return Token(ttype, word, start_line, start_col)

    def read_line_comment(self):
        while self.pos < len(self.source) and self.peek() != "\n":
            self.advance()

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.peek()
            start_line, start_col = self.line, self.col

            if ch == "\n":
                self.advance()
                continue

            elif ch == "/" and self.peek(1) == "/":
                self.advance(); self.advance()
                self.read_line_comment()
                continue

            elif ch == "#":
                self.advance()
                self.read_line_comment()
                continue

            elif ch == '"':
                self.tokens.append(self.read_string())

            elif ch.isdigit():
                self.tokens.append(self.read_number())

            elif ch.isalpha() or ch == "_":
                self.tokens.append(self.read_identifier())

            elif ch == "{":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, "{", start_line, start_col))
            elif ch == "}":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, "}", start_line, start_col))
            elif ch == "[":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == "]":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == ",":
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == ";":
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ";", start_line, start_col))
            elif ch == ".":
                self.advance()
                self.tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            elif ch == ">":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.GTE, ">=", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.GT, ">", start_line, start_col))
            elif ch == "<":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.LTE, "<=", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT, "<", start_line, start_col))
            elif ch == "=":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.EQ, "==", start_line, start_col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", start_line, start_col))
            elif ch == "!":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.NEQ, "!=", start_line, start_col))
                else:
                    raise self.error(f"Unexpected character '!'")
            else:
                raise self.error(f"Unexpected character: {ch!r}")

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens
