from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from antlr4 import FileStream, CommonTokenStream, ParserRuleContext, Token
from antlr4.error.ErrorListener import ErrorListener

from CompiscriptLexer import CompiscriptLexer
from CompiscriptParser import CompiscriptParser


@dataclass
class SyntaxIssue:
    line: int
    column: int
    message: str


class CollectingErrorListener(ErrorListener):
    def __init__(self) -> None:
        super().__init__()
        self.issues: List[SyntaxIssue] = []

    def syntaxError(self, recognizer, offendingSymbol: Optional[Token], line, column, msg, e):
        self.issues.append(SyntaxIssue(line=line, column=column, message=str(msg)))


@dataclass
class ParseResult:
    tree: ParserRuleContext
    parser: CompiscriptParser
    issues: List[SyntaxIssue]


def parse_file(path: str) -> ParseResult:
    """
    Parsea un archivo .cps y retorna el árbol, el parser y los errores sintácticos (si hay).
    """
    # 1) stream -> lexer -> tokens
    stream = FileStream(path, encoding="utf-8")
    lexer = CompiscriptLexer(stream)
    tokens = CommonTokenStream(lexer)

    # 2) parser + listener de errores
    parser = CompiscriptParser(tokens)
    listener = CollectingErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    # 3) regla inicial (ajusta si tu gramática usa otro nombre)
    #   Suele ser 'program' en este proyecto.
    tree = parser.program()

    return ParseResult(tree=tree, parser=parser, issues=listener.issues)


def tree_as_lisp(result: ParseResult) -> str:
    """
    Retorna el árbol en notación S-expression usando los nombres de las reglas del parser.
    """
    return result.tree.toStringTree(recog=result.parser)