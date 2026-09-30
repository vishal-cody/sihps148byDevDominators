"""JOCKY compiler tests — Lexer"""
import pytest
from compiler.lexer import Lexer, TokenType, LexerError


def test_basic_keywords():
    tokens = Lexer('investigation "Test" { collect processes }').tokenize()
    types = [t.type for t in tokens]
    assert TokenType.INVESTIGATION in types
    assert TokenType.STRING in types
    assert TokenType.LBRACE in types
    assert TokenType.COLLECT in types
    assert TokenType.PROCESSES in types
    assert TokenType.RBRACE in types
    assert TokenType.EOF in types


def test_string_literal():
    tokens = Lexer('"Hello World"').tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "Hello World"


def test_all_collectors():
    src = "collect processes collect network_connections collect system_info collect event_logs collect persistence collect filesystem"
    tokens = Lexer(src).tokenize()
    collector_types = [t.type for t in tokens if t.type not in (TokenType.COLLECT, TokenType.EOF)]
    expected = [TokenType.PROCESSES, TokenType.NETWORK_CONNECTIONS, TokenType.SYSTEM_INFO,
                TokenType.EVENT_LOGS, TokenType.PERSISTENCE, TokenType.FILESYSTEM]
    assert collector_types == expected


def test_operators():
    tokens = Lexer('cpu > 50').tokenize()
    assert tokens[1].type == TokenType.GT

    tokens = Lexer('port in [4444]').tokenize()
    assert tokens[1].type == TokenType.IN


def test_comments_ignored():
    tokens = Lexer('// this is a comment\ncollect processes').tokenize()
    types = [t.type for t in tokens]
    assert TokenType.COLLECT in types
    assert TokenType.COMMENT not in types


def test_unterminated_string():
    with pytest.raises(LexerError):
        Lexer('"unterminated').tokenize()


def test_line_col_tracking():
    tokens = Lexer('investigation "Test" {\n    collect processes\n}').tokenize()
    collect_token = next(t for t in tokens if t.type == TokenType.COLLECT)
    assert collect_token.line == 2
