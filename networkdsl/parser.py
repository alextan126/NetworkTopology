"""Recursive-descent parser for the network topology DSL."""

from __future__ import annotations

from typing import Dict, List, Optional

from .ast import (
    ConnectExpr,
    DegreeCriteriaExpr,
    Expression,
    IdentifierExpr,
    LetStatement,
    MotifExpr,
    MotifKind,
    NodeRefLiteral,
    OverlayExpr,
    PickExpr,
    Program,
    RelabelExpr,
    RequireExpr,
    SourceLocation,
)
from .lexer import Lexer, LexerError, Token, TokenType
from .types import NodeId

__all__ = ["ParserError", "Parser", "parse_program"]


class ParserError(ValueError):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._current = 0

    def parse(self) -> Program:
        statements: List[LetStatement] = []
        while self._match(TokenType.LET):
            statements.append(self._parse_let())
        expression: Optional[Expression] = None
        if not self._check(TokenType.EOF):
            expression = self._expression()
        self._consume(TokenType.EOF, "Expected end of input.")
        return Program(statements, expression)

    def _parse_let(self) -> LetStatement:
        let_token = self._previous()
        name_token = self._consume(TokenType.IDENT, "Expected identifier after 'let'.")
        self._consume(TokenType.EQUAL, "Expected '=' in let binding.")
        expr = self._expression()
        return LetStatement(name_token.lexeme, expr, self._location(let_token))

    def _expression(self) -> Expression:
        token = self._peek()
        if token.type in (TokenType.RING, TokenType.PATH, TokenType.STAR, TokenType.MESH):
            return self._motif_expression()
        if token.type == TokenType.CONNECT:
            return self._connect_expression()
        if token.type == TokenType.OVERLAY:
            return self._overlay_expression()
        if token.type == TokenType.RELABEL:
            return self._relabel_expression()
        if token.type == TokenType.PICK:
            return self._pick_expression()
        if token.type == TokenType.REQUIRE:
            return self._require_expression()
        if token.type == TokenType.IDENT:
            ident_token = self._advance()
            return IdentifierExpr(ident_token.lexeme, self._location(ident_token))
        raise ParserError(f"Unexpected token {token.type.name} at line {token.line}, column {token.column}.")

    def _motif_expression(self) -> MotifExpr:
        token = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after motif keyword.")
        size_token = self._consume(TokenType.INT, "Motif requires integer size parameter.")
        self._consume(TokenType.RPAREN, "Expected ')' after motif argument.")
        kind = {
            TokenType.RING: MotifKind.RING,
            TokenType.PATH: MotifKind.PATH,
            TokenType.STAR: MotifKind.STAR,
            TokenType.MESH: MotifKind.MESH,
        }[token.type]
        return MotifExpr(kind, size_token.literal or 0, self._location(token))

    def _overlay_expression(self) -> OverlayExpr:
        keyword = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after Overlay.")
        left = self._expression()
        self._consume(TokenType.COMMA, "Expected ',' between Overlay arguments.")
        right = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after Overlay arguments.")
        return OverlayExpr(left, right, self._location(keyword))

    def _connect_expression(self) -> ConnectExpr:
        keyword = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after Connect.")
        left = self._expression()
        self._consume(TokenType.COMMA, "Expected ',' after first Connect argument.")
        right = self._expression()
        self._consume(TokenType.COMMA, "Expected ',' after second Connect argument.")
        bridge_token = self._consume(TokenType.IDENT, "Expected 'bridge' keyword.")
        if bridge_token.lexeme != "bridge":
            raise ParserError(
                f"Expected named argument 'bridge', found {bridge_token.lexeme!r}."
            )
        self._consume(TokenType.EQUAL, "Expected '=' after bridge.")
        self._consume(TokenType.LPAREN, "Expected '(' starting bridge tuple.")
        left_ref = self._node_ref()
        self._consume(TokenType.COMMA, "Expected ',' between bridge node references.")
        right_ref = self._node_ref()
        self._consume(TokenType.RPAREN, "Expected ')' after bridge tuple.")
        self._consume(TokenType.RPAREN, "Expected ')' to close Connect.")
        return ConnectExpr(left, right, left_ref, right_ref, self._location(keyword))

    def _node_ref(self) -> NodeRefLiteral:
        ident_token = self._consume(TokenType.IDENT, "Expected graph identifier in node reference.")
        self._consume(TokenType.DOT, "Expected '.' in node reference.")
        index_token = self._consume(TokenType.INT, "Expected node index after '.'.")
        return NodeRefLiteral(
            ident_token.lexeme,
            NodeId(index_token.literal or 0),
            self._location(ident_token),
        )

    def _relabel_expression(self) -> RelabelExpr:
        keyword = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after Relabel.")
        target = self._expression()
        self._consume(TokenType.COMMA, "Expected ',' between Relabel arguments.")
        mapping = self._mapping_literal()
        self._consume(TokenType.RPAREN, "Expected ')' to close Relabel.")
        return RelabelExpr(target, mapping, self._location(keyword))

    def _mapping_literal(self) -> Dict[NodeId, NodeId]:
        mapping: Dict[NodeId, NodeId] = {}
        self._consume(TokenType.LBRACE, "Expected '{' to start mapping literal.")
        if not self._check(TokenType.RBRACE):
            while True:
                source = self._consume(TokenType.INT, "Expected source node id in mapping.")
                self._consume(TokenType.COLON, "Expected ':' in mapping entry.")
                target = self._consume(TokenType.INT, "Expected target node id in mapping.")
                mapping[NodeId(source.literal or 0)] = NodeId(target.literal or 0)
                if not self._match(TokenType.COMMA):
                    break
        self._consume(TokenType.RBRACE, "Expected '}' after mapping literal.")
        return mapping

    def _pick_expression(self) -> PickExpr:
        keyword = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after Pick.")
        target = self._expression()
        self._consume(TokenType.COMMA, "Expected ',' between Pick arguments.")
        criteria = self._criteria_literal()
        self._consume(TokenType.RPAREN, "Expected ')' after Pick arguments.")
        return PickExpr(target, criteria, self._location(keyword))

    def _criteria_literal(self) -> DegreeCriteriaExpr:
        name = self._consume(TokenType.IDENT, "Expected criteria name (e.g. deg).")
        if name.lexeme != "deg":
            raise ParserError(f"Unsupported criteria {name.lexeme!r}.")
        self._consume(TokenType.EQUAL, "Expected '=' in criteria.")
        value_token = self._consume(TokenType.INT, "Expected integer degree value.")
        return DegreeCriteriaExpr(value_token.literal or 0, self._location(name))

    def _require_expression(self) -> RequireExpr:
        keyword = self._advance()
        self._consume(TokenType.LPAREN, "Expected '(' after Require.")
        target = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' to close Require.")
        return RequireExpr(target, self._location(keyword))

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise ParserError(f"{message} Found {token.type.name} at line {token.line}, column {token.column}.")

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return token_type == TokenType.EOF
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._current]

    def _previous(self) -> Token:
        return self._tokens[self._current - 1]

    def _location(self, token: Token) -> SourceLocation:
        return SourceLocation(token.line, token.column)


def parse_program(source: str) -> Program:
    try:
        tokens = Lexer(source).tokenize()
    except LexerError as error:
        raise ParserError(str(error)) from error

    parser = Parser(tokens)
    return parser.parse()

