"""Lexical analysis for the network topology DSL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

__all__ = ["TokenType", "Token", "Lexer", "LexerError"]


class LexerError(ValueError):
    pass


class TokenType(Enum):
    IDENT = auto()
    INT = auto()
    LET = auto()
    RING = auto()
    PATH = auto()
    STAR = auto()
    MESH = auto()
    CONNECT = auto()
    OVERLAY = auto()
    RELABEL = auto()
    PICK = auto()
    REQUIRE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    EQUAL = auto()
    DOT = auto()
    EOF = auto()


KEYWORDS = {
    "let": TokenType.LET,
    "Ring": TokenType.RING,
    "Path": TokenType.PATH,
    "Star": TokenType.STAR,
    "Mesh": TokenType.MESH,
    "Connect": TokenType.CONNECT,
    "Overlay": TokenType.OVERLAY,
    "Relabel": TokenType.RELABEL,
    "Pick": TokenType.PICK,
    "Require": TokenType.REQUIRE,
}


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Optional[int]
    line: int
    column: int


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self._start = 0
        self._current = 0
        self._line = 1
        self._column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            self._start = self._current
            self._skip_whitespace()
            if self._is_at_end():
                break
            self._start = self._current
            char = self._advance()
            if char.isalpha() or char == "_":
                tokens.append(self._identifier())
            elif char.isdigit():
                tokens.append(self._number())
            else:
                token = self._punctuation(char)
                if token is None:
                    raise LexerError(
                        f"Unexpected character {char!r} at line {self._line}, column {self._column - 1}"
                    )
                tokens.append(token)
        tokens.append(Token(TokenType.EOF, "", None, self._line, self._column))
        return tokens

    def _skip_whitespace(self) -> None:
        while not self._is_at_end():
            char = self._peek()
            if char in (" ", "\r", "\t"):
                self._advance()
            elif char == "\n":
                self._advance()
                self._line += 1
                self._column = 1
            else:
                break

    def _identifier(self) -> Token:
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        lexeme = self.source[self._start:self._current]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENT)
        return Token(token_type, lexeme, None, self._line, self._token_column())

    def _number(self) -> Token:
        while not self._is_at_end() and self._peek().isdigit():
            self._advance()
        lexeme = self.source[self._start:self._current]
        value = int(lexeme)
        return Token(TokenType.INT, lexeme, value, self._line, self._token_column())

    def _punctuation(self, char: str) -> Optional[Token]:
        mapping = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            "=": TokenType.EQUAL,
            ".": TokenType.DOT,
        }
        token_type = mapping.get(char)
        if token_type is None:
            return None
        return Token(token_type, char, None, self._line, self._token_column())

    def _advance(self) -> str:
        char = self.source[self._current]
        self._current += 1
        self._column += 1
        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self._current]

    def _is_at_end(self) -> bool:
        return self._current >= len(self.source)

    def _token_column(self) -> int:
        return self._column - (self._current - self._start)

